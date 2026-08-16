"""Running the pipeline, streamed.

Server-sent events so the UI shows the state as it is built, and the same story printed
to the server console so you can watch it there too.
"""

import json
import time
import traceback
from collections import Counter
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.api.deps import get_project_or_404
from app.graph.pipeline import pipeline, unfinished
from app.storage import store
from app.tools import ingest

router = APIRouter(prefix="/api/projects/{pid}", tags=["run"])


def sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def events(project: dict) -> Iterator[str]:
    pid = project["id"]
    started = time.monotonic()

    def trace(line: str) -> None:
        # plain print, flushed — this lands in the uvicorn console you already have open
        print(f"  [{pid[:6]} {time.monotonic() - started:5.1f}s] {line}", flush=True)

    def emit(payload: dict, line: str) -> str:
        trace(line)
        return sse(payload)

    # a previous run that died mid-flight left its finished nodes on disk
    pending = unfinished(pid)
    trace(f"── run start · {project['name']} · {len(project['inputs'])} inputs " + "─" * 20)
    yield sse({"event": "start", "inputs": len(project["inputs"]), "resuming": list(pending)})

    if pending:
        trace(f"resume  picking up from {', '.join(pending)} — earlier nodes are cached")

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
        yield emit({"event": "error", "message": "nothing could be parsed yet"}, "nothing to parse")
        return

    sources = len({c.source_id for c in chunks})
    yield emit(
        {"event": "node_start", "node": "extract", "chunks": len(chunks), "sources": sources},
        f"node  extract x{sources} in parallel ← state: chunks={len(chunks)} findings=0",
    )

    findings, insights, gaps, faults = [], [], [], []
    brief = proposal = outline = None
    prototype = False

    try:
        # .stream() hands back each task as it finishes, so sources report one by one
        # instead of the whole thing landing at the end
        # Passing None resumes a checkpointed run from where it stopped; passing state
        # starts a fresh one. thread_id is the project, so one run per project at a time.
        config = {"configurable": {"thread_id": pid}}
        start_from = None if pending else {"project_id": pid, "chunks": chunks, "findings": []}

        for update in pipeline.stream(start_from, config):
            for node, produced in update.items():
                if node == "extract":
                    # each update carries only that task's findings; operator.add merges
                    # them into graph state, but we accumulate our own copy for the UI
                    batch = produced.get("findings", [])
                    findings.extend(batch)
                    source = batch[0].source_id if batch else "?"
                    yield emit(
                        {
                            "event": "node_done",
                            "node": node,
                            "source": source,
                            "findings": len(batch),
                            "total": len(findings),
                        },
                        f"node  extract({source}) → {len(batch)} findings"
                        f"  {dict(Counter(f.type for f in batch))}  ·  total {len(findings)}",
                    )
                    for finding in batch:
                        trace(f"        {finding.type:11} {finding.text[:86]}")

                elif node == "merge":
                    insights = produced["insights"]
                    corroborated = sum(1 for i in insights if len(i.sources) > 1)
                    yield emit(
                        {
                            "event": "merged",
                            "insights": len(insights),
                            "collapsed": len(findings) - len(insights),
                            "corroborated": corroborated,
                        },
                        f"node  merge → {len(findings)} findings collapsed to {len(insights)}"
                        f" insights, {corroborated} backed by more than one source",
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
                        f"node  synthesize → brief: {len(brief.current_process)} process steps, "
                        f"{len(brief.pain_points)} pains, {len(brief.requirements)} requirements",
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
                        f"node  find_gaps → {len(gaps)} open questions "
                        f"{dict(Counter(g.kind for g in gaps))}",
                    )
                    for gap in gaps:
                        trace(f"        {gap.kind:15} {gap.question[:84]}")

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
                        f"node  redesign → {len(proposal.to_be)} steps {dict(changes)}, "
                        f"{len(proposal.not_solved)} pains left unsolved",
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
                        f"node  outline → '{outline.app_name}': {len(outline.roles)} roles, "
                        f"{len(outline.features)} features, {len(outline.screens)} screens",
                    )

                elif node == "prototype":
                    html = produced["prototype"]
                    faults = produced["prototype_faults"]
                    prototype = not faults
                    if prototype:
                        store.save_prototype(pid, html)
                    yield emit(
                        {"event": "prototype", "ok": prototype, "bytes": len(html), "faults": faults},
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

    # Read the finished state from the checkpoint rather than from what we accumulated:
    # on a resumed run the already-completed nodes emit no events, so the local copies
    # would be missing everything the previous attempt produced.
    final = pipeline.get_state(config).values

    def dump(key: str):
        value = final.get(key)
        if value is None:
            return None
        return [v.model_dump() for v in value] if isinstance(value, list) else value.model_dump()

    result = {
        "chunks": dump("chunks") or [],
        "findings": dump("findings") or [],
        "insights": dump("insights") or [],
        "brief": dump("brief"),
        "gaps": dump("gaps") or [],
        "redesign": dump("redesign"),
        "outline": dump("outline"),
        # the HTML itself lives in prototype.html; run.json only records whether it is usable
        "prototype": prototype or bool(final.get("prototype")) and not final.get("prototype_faults"),
        "prototype_faults": faults or final.get("prototype_faults", []),
    }
    store.save_run(pid, result)
    trace(f"── run done · saved to data/{pid}/run.json " + "─" * 24)
    yield sse({"event": "done", **result})


@router.post("/run")
def run_discovery(project: dict = Depends(get_project_or_404)):
    return StreamingResponse(
        events(project),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/run")
def last_run(project: dict = Depends(get_project_or_404)):
    result = store.load_run(project["id"])
    if not result:
        raise HTTPException(404, "no run yet")
    return result


@router.get("/prototype")
def prototype(project: dict = Depends(get_project_or_404)):
    """The generated demo. Served as its own document so the UI can iframe it."""
    path = store.prototype_path(project["id"])
    if not path.exists():
        raise HTTPException(404, "no prototype yet")
    return FileResponse(path, media_type="text/html")
