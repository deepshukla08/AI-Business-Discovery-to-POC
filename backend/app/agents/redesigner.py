"""Agent 5 — the brief in, a simpler way of working out."""

from pathlib import Path

from app.agents import citations, llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Answer, Brief, Gap, Redesign

PROMPT = (Path(__file__).parent / "prompts" / "redesigner.md").read_text(encoding="utf-8")


def render_gaps(gaps: list[Gap], answered: set[str]) -> str:
    open_gaps = [g for g in gaps if g.question not in answered]
    if not open_gaps:
        return "(none — everything raised has been answered)"
    return "\n".join(f"- [{g.kind}] {g.question} — {g.why_it_matters}" for g in open_gaps)


def render_answers(answers: list[Answer]) -> str:
    if not answers:
        return "(none — the client has not come back on any of the open questions)"
    return "\n".join(f"- Q: {a.question}\n  A: {a.answer}" for a in answers)


def redesign(
    brief: Brief, gaps: list[Gap], answers: list[Answer], valid_ids: set[str]
) -> Redesign:
    answered = {a.question for a in answers}
    prompt = (
        PROMPT.replace("{{BRIEF}}", brief.model_dump_json(indent=2))
        .replace("{{ANSWERS}}", render_answers(answers))
        # a question the client has answered is no longer an unknown to design around
        .replace("{{GAPS}}", render_gaps(gaps, answered))
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
    return {
        "redesign": redesign(
            state["brief"], state.get("gaps", []), state.get("answers", []), valid_ids
        )
    }
