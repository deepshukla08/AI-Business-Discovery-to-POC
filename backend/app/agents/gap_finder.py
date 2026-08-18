"""Agent 4 — what the client never told us.

The hardest agent, and the one worth the most. A summary of what was said is easy; noticing
what was never said takes reading everything at once and knowing what should have been there.
"""

from pathlib import Path

from app.agents import llm, synthesizer
from app.graph.state import DiscoveryState
from app.schemas.discovery import Brief, Gap, Insight

PROMPT = (Path(__file__).parent / "prompts" / "gap_finder.md").read_text(encoding="utf-8")


def find(insights: list[Insight], brief: Brief, valid_ids: set[str]) -> list[Gap]:
    prompt = PROMPT.replace("{{BRIEF}}", brief.model_dump_json(indent=2)).replace(
        "{{FINDINGS}}", synthesizer.render(insights)
    )
    # HIGH: the only agent that has to reason about absence and contradiction across every
    # source at once. This is where thinking budget actually buys something.
    gaps: list[Gap] = llm.generate_json(prompt, list[Gap], thinking="HIGH") or []

    kept = []
    for gap in gaps:
        gap.cites = [cite for cite in gap.cites if cite in valid_ids]
        # a claim about the record must point at the record; only an absence may be uncited
        if gap.cites or gap.kind == "never_discussed":
            kept.append(gap)
    return kept


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    valid_ids = {chunk.id for chunk in state["chunks"]}
    return {"gaps": find(state["insights"], state["brief"], valid_ids)}
