"""Running the pipeline, streamed.

Server-sent events so the UI shows the state as it is built, and the same story printed
to the server console so you can watch it there too.

The run stops at `ask_client` and waits. The browser posts answers to /run/answers, which
resumes the same checkpointed run rather than starting a new one.
"""

import json
import time
import traceback
from collections import Counter
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel

from app.api.deps import get_project_or_404
from app.graph.pipeline import pipeline, unfinished
from app.storage import store
from app.tools import ingest

router = APIRouter(prefix="/api/projects/{pid}", tags=["run"])


class Reply(BaseModel):
    question: str
    answer: str


class Answers(BaseModel):
    answers: list[Reply] = []


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def collect(pid: str) -> dict:
    """Build the run result from the checkpoint.

    Deliberately not from what the event handler accumulated: on a resumed run the nodes
    that already finished emit nothing, so that copy would be missing everything the
    previous attempt produced.
    """
    final = pipeline.get_state({"configurable": {"thread_id": pid}}).values

    def dump(key: str):
        value = final.get(key)
        if value is None:
            return None
        return [v.model_dump() for v in value] if isinstance(value, list) else value.model_dump()

    html_faults = final.get("prototype_faults")
    return {
        "chunks": dump("chunks") or [],
        "findings": dump("findings") or [],
        "insights": dump("insights") or [],
        "brief": dump("brief"),
        "gaps": dump("gaps") or [],
        "answers": dump("answers") or [],
        "redesign": dump("redesign"),
        "outline": dump("outline"),
        # the HTML itself lives in prototype.html; run.json only records whether it is usable
        "prototype": bool(final.get("prototype")) and not html_faults,
        "prototype_faults": html_faults or [],
    }


def events(project: dict, resume_with: list[dict] | None = None) -> Iterator[str]:
    pid = project["id"]
    config = {"configurable": {"thread_id": pid}}
    started = time.monotonic()

    def trace(line: str) -> None:
        # plain print, flushed — this lands in the uvicorn console you already have open
        print(f"  [{pid[:6]} {time.monotonic() - started:5.1f}s] {line}", flush=True)

    def emit(payload: dict, line: str) -> str:
        trace(line)
        return sse(payload)

    if resume_with is not None:
        trace(f"── resume with {len(resume_with)} answers " + "─" * 30)
        yield sse({"event": "start", "inputs": len(project["inputs"]), "resuming": ["answers"]})
        start_from = Command(resume=resume_with)
    else:
        # a previous run that died mid-flight left its finished nodes on disk
        pending = unfinished(pid)
        trace(f"── run start · {project['name']} · {len(project['inputs'])} inputs " + "─" * 18)
        yield sse({"event": "start", "inputs": len(project["inputs"]), "resuming": list(pending)})

        if pending:
            trace(f"resume  picking up from {', '.join(pending)} — earlier nodes are cached")
            start_from = None
        else:
            chunks = []
            for record in project["inputs"]:
                parsed, skipped = ingest.parse_input(pid, record)
                if skipped:
                    yield emit(
                        {"event": "skipped", "label": record["label"], "reason": skipped},
                        f"skip  {record['label']} — {skipped}",
                    )
                else:
                    chunks.extend(parsed)
                    yield emit(
                        {
                            "event": "parsed",
                            "label": record["label"],
                            "kind": record["kind"],
                            "chunks": len(parsed),
                        },
                        f"parse {record['label']} ({record['kind']}) → {len(parsed)} chunks"
                        f"  [{parsed[0].id}…{parsed[-1].id}]",
                    )

            if not chunks:
                yield emit(
                    {"event": "error", "message": "nothing could be parsed yet"},
                    "nothing to parse",
                )
                return

            sources = len({c.source_id for c in chunks})
            yield emit(
                {
                    "event": "node_start",
                    "node": "extract",
                    "chunks": len(chunks),
                    "sources": sources,
                },
                f"node  extract x{sources} in parallel ← chunks={len(chunks)}",
            )
            start_from = {"project_id": pid, "chunks": chunks, "findings": []}

    total_findings = 0
    try:
        # .stream() hands back each task as it finishes, so sources report one by one
        # instead of the whole thing landing at the end
        for update in pipeline.stream(start_from, config):
            # the graph paused at ask_client; hand the questions over and stop the stream
            if "__interrupt__" in update:
                paused = update["__interrupt__"][0].value
                partial = collect(pid)
                store.save_run(pid, partial)
                yield emit(
                    {"event": "awaiting", **partial},
                    f"pause  waiting on {len(paused.get('gaps', []))} answers "
                    f"— nothing below this point is decided yet",
                )
                return

            for node, produced in update.items():
                if node == "extract":
                    batch = produced.get("findings", [])
                    total_findings += len(batch)
                    source = batch[0].source_id if batch else "?"
                    yield emit(
                        {
                            "event": "node_done",
                            "node": node,
                            "source": source,
                            "findings": len(batch),
                            "total": total_findings,
                        },
                        f"node  extract({source}) → {len(batch)} findings"
                        f"  {dict(Counter(f.type for f in batch))}",
                    )

                elif node == "merge":
                    insights = produced["insights"]
                    corroborated = sum(1 for i in insights if len(i.sources) > 1)
                    yield emit(
                        {
                            "event": "merged",
                            "insights": len(insights),
                            "collapsed": max(total_findings - len(insights), 0),
                            "corroborated": corroborated,
                        },
                        f"node  merge → {len(insights)} insights, "
                        f"{corroborated} backed by more than one source",
                    )

                elif node == "synthesize":
                    brief = produced["brief"]
                    yield emit(
                        {
                            "event": "brief",
                            "pains": len(brief.pain_points),
                            "steps": len(brief.current_process),
                            "requirements": len(brief.requirements),
                        },
                        f"node  synthesize → {len(brief.current_process)} process steps, "
                        f"{len(brief.pain_points)} pains",
                    )
                    trace(f"        GOAL  {brief.goal.text[:150]}")

                elif node == "find_gaps":
                    gaps = produced["gaps"]
                    yield emit(
                        {
                            "event": "gaps",
                            "gaps": len(gaps),
                            "kinds": dict(Counter(g.kind for g in gaps)),
                        },
                        f"node  find_gaps → {len(gaps)} open questions",
                    )
                    for gap in gaps:
                        trace(f"        {gap.kind:15} {gap.question[:84]}")

                elif node == "ask_client":
                    answers = produced.get("answers", [])
                    yield emit(
                        {"event": "answered", "answers": len(answers)},
                        f"node  ask_client → {len(answers)} answered, continuing",
                    )

                elif node == "redesign":
                    proposal = produced["redesign"]
                    changes = Counter(step.change for step in proposal.to_be)
                    yield emit(
                        {
                            "event": "redesign",
                            "steps": len(proposal.to_be),
                            "changes": dict(changes),
                            "not_solved": len(proposal.not_solved),
                        },
                        f"node  redesign → {len(proposal.to_be)} steps {dict(changes)}",
                    )
                    trace(f"        {proposal.summary[:150]}")

                elif node == "outline":
                    outline = produced["outline"]
                    yield emit(
                        {
                            "event": "outline",
                            "app_name": outline.app_name,
                            "roles": len(outline.roles),
                            "features": len(outline.features),
                            "screens": len(outline.screens),
                        },
                        f"node  outline → '{outline.app_name}': {len(outline.screens)} screens",
                    )

                elif node == "prototype":
                    html = produced["prototype"]
                    faults = produced["prototype_faults"]
                    if not faults:
                        store.save_prototype(pid, html)
                    yield emit(
                        {
                            "event": "prototype",
                            "ok": not faults,
                            "bytes": len(html),
                            "faults": faults,
                        },
                        f"node  prototype → {len(html):,} bytes"
                        + (f"  REJECTED: {'; '.join(faults)}" if faults else "  looks usable"),
                    )

    except Exception as failure:  # surface it in the UI instead of a dead stream
        traceback.print_exc()
        yield emit(
            {"event": "error", "message": f"{type(failure).__name__}: {failure}"},
            f"FAILED {type(failure).__name__}: {failure}",
        )
        return

    result = collect(pid)
    store.save_run(pid, result)
    trace(f"── run done · saved to data/{pid}/run.json " + "─" * 24)
    yield sse({"event": "done", **result})


def stream(project: dict, resume_with: list[dict] | None = None) -> StreamingResponse:
    return StreamingResponse(
        events(project, resume_with),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/run")
def run_discovery(project: dict = Depends(get_project_or_404)):
    return stream(project)


@router.post("/run/answers")
def answer_and_continue(body: Answers, project: dict = Depends(get_project_or_404)):
    """Resume a paused run. An empty list means 'proceed without answers' — a deliberate
    choice by the consultant, which is different from never having been asked."""
    if "ask_client" not in unfinished(project["id"]):
        raise HTTPException(409, "this run is not waiting for answers")
    return stream(project, [reply.model_dump() for reply in body.answers])


@router.get("/run")
def last_run(project: dict = Depends(get_project_or_404)):
    result = store.load_run(project["id"])
    if not result:
        raise HTTPException(404, "no run yet")
    result["awaiting"] = "ask_client" in unfinished(project["id"])
    return result


@router.get("/prototype")
def prototype(project: dict = Depends(get_project_or_404)):
    """The generated demo. Served as its own document so the UI can iframe it."""
    path = store.prototype_path(project["id"])
    if not path.exists():
        raise HTTPException(404, "no prototype yet")
    return FileResponse(path, media_type="text/html")
