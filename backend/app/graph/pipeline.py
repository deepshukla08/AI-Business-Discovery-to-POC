"""The discovery pipeline.

    START ──┬── extract(call_1)     ┐
            ├── extract(call_2)     │  in parallel, one per source
            ├── extract(whatsapp)   ├─ findings merge via operator.add
            ├── extract(pdf)        │
            └── extract(screenshot) ┘
                     │
                   merge          collapse duplicates, count corroboration (no model)
                     │
                 synthesize       the discovery brief
                     │
                  find_gaps       what the client never told us
                     │
                  redesign        a simpler way of working
                     │
                   outline        features, roles, screens, flow
                     │
                  prototype       a self-contained clickable HTML demo
                     │
                    END

ponytail: linear from find_gaps on. Step 9 puts an interrupt() between find_gaps and
redesign so a consultant can answer the open questions before a proposal is built on
guesses — that is the whole reason LangGraph is here rather than a chain of functions.
"""

import sqlite3
from collections import defaultdict

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel

from app.config import DATA_DIR
from app.schemas import discovery

from app.agents import (
    extractor,
    gap_finder,
    merger,
    outliner,
    prototyper,
    redesigner,
    synthesizer,
)
from app.graph.state import DiscoveryState


def fan_out(state: DiscoveryState) -> list[Send]:
    """One extractor per source.

    The extractor is written to read a single source — it names that source in its prompt
    and stamps it on every finding. Handing it four documents at once made both a lie.
    """
    by_source: dict[str, list] = defaultdict(list)
    for chunk in state["chunks"]:
        by_source[chunk.source_id].append(chunk)

    # project_id rides along so an image chunk can be resolved back to its file
    return [
        Send("extract", {"project_id": state["project_id"], "chunks": chunks})
        for chunks in by_source.values()
    ]


builder = StateGraph(DiscoveryState)
builder.add_node("extract", extractor.run)
builder.add_node("merge", merger.run)
builder.add_node("synthesize", synthesizer.run)
builder.add_node("find_gaps", gap_finder.run)
builder.add_node("redesign", redesigner.run)
builder.add_node("outline", outliner.run)
builder.add_node("prototype", prototyper.run)

builder.add_conditional_edges(START, fan_out, ["extract"])
builder.add_edge("extract", "merge")
builder.add_edge("merge", "synthesize")
builder.add_edge("synthesize", "find_gaps")
builder.add_edge("find_gaps", "redesign")
builder.add_edge("redesign", "outline")
builder.add_edge("outline", "prototype")
builder.add_edge("prototype", END)

# Only our own schemas may come back out of the checkpoint file. Without an allowlist
# LangGraph deserialises any type it finds — fine until someone can write to the file —
# and it warns that permissive mode will stop working in a future version.
# Collected by introspection so adding a schema does not mean remembering to list it.
ALLOWED = [
    value
    for value in vars(discovery).values()
    if isinstance(value, type)
    and issubclass(value, BaseModel)
    # defined here, not merely imported — otherwise pydantic's own BaseModel joins the list
    and value.__module__ == discovery.__name__
]

# State is written to disk after every node. A run killed halfway — a refresh, a crash,
# a dropped connection — resumes from the last completed node instead of repaying the
# extract calls. check_same_thread=False because the fan-out runs nodes in threads.
_connection = sqlite3.connect(DATA_DIR / "checkpoints.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(_connection, serde=JsonPlusSerializer(allowed_msgpack_modules=ALLOWED))

pipeline = builder.compile(checkpointer=checkpointer)


def unfinished(thread_id: str) -> tuple[str, ...]:
    """Which nodes a previous run left pending. Empty means nothing to resume."""
    state = pipeline.get_state({"configurable": {"thread_id": thread_id}})
    return tuple(state.next)
