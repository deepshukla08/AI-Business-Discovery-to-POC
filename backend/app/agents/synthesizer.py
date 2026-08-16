"""Agent 3 — merged insights in, a discovery brief out."""

from pathlib import Path

from app.agents import citations, llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Brief, Insight

PROMPT = (Path(__file__).parent / "prompts" / "synthesizer.md").read_text(encoding="utf-8")


def render(insights: list[Insight]) -> str:
    return "\n".join(
        f"[{','.join(i.cites)}] ({len(i.sources)} src) {i.type.upper()} — {i.text}"
        for i in insights
    )


def synthesize(insights: list[Insight], valid_ids: set[str]) -> Brief:
    prompt = PROMPT.replace("{{FINDINGS}}", render(insights))
    # MEDIUM: this is judgment — deciding what the goal really is, and what ranks above
    # what — but it is judgment over evidence already gathered, not fresh reasoning.
    brief: Brief = llm.generate_json(prompt, Brief, thinking="MEDIUM")

    brief.goal.cites = [c for c in brief.goal.cites if c in valid_ids]
    for section in ("current_process", "pain_points", "requirements", "constraints", "stated_wants"):
        # the process is a sequence: dropping an uncited step would leave a gap in the
        # story rather than remove a claim, so those are kept and simply uncited
        setattr(
            brief,
            section,
            citations.enforce(
                getattr(brief, section),
                valid_ids,
                allow_uncited=section == "current_process",
            ),
        )
    return brief


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    valid_ids = {chunk.id for chunk in state["chunks"]}
    return {"brief": synthesize(state["insights"], valid_ids)}
