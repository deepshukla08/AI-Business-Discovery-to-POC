"""Agent 5 — the brief in, a simpler way of working out."""

from pathlib import Path

from app.agents import citations, llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Brief, Gap, Redesign

PROMPT = (Path(__file__).parent / "prompts" / "redesigner.md").read_text(encoding="utf-8")


def render_gaps(gaps: list[Gap]) -> str:
    if not gaps:
        return "(none identified)"
    return "\n".join(f"- [{g.kind}] {g.question} — {g.why_it_matters}" for g in gaps)


def redesign(brief: Brief, gaps: list[Gap], valid_ids: set[str]) -> Redesign:
    prompt = PROMPT.replace("{{BRIEF}}", brief.model_dump_json(indent=2)).replace(
        "{{GAPS}}", render_gaps(gaps)
    )
    # MEDIUM: real design judgment, but every input is already established — it is
    # rearranging known facts, not reasoning about what is missing.
    proposal: Redesign = llm.generate_json(prompt, Redesign, thinking="MEDIUM")

    # a proposed step may legitimately be new and cite nothing; a claim about what the
    # change wins or fails to win must point at the pain it refers to
    proposal.to_be = citations.enforce(proposal.to_be, valid_ids, allow_uncited=True)
    proposal.wins = citations.enforce(proposal.wins, valid_ids)
    proposal.not_solved = citations.enforce(proposal.not_solved, valid_ids)
    return proposal


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    valid_ids = {chunk.id for chunk in state["chunks"]}
    return {"redesign": redesign(state["brief"], state.get("gaps", []), valid_ids)}
