"""Agent 6 — the proposed process in, an application outline out.

Its output is the prototyper's input, so vagueness here becomes a broken demo.
"""

from pathlib import Path

from app.agents import llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Brief, Outline, Redesign

PROMPT = (Path(__file__).parent / "prompts" / "outliner.md").read_text(encoding="utf-8")


def outline(proposal: Redesign, brief: Brief) -> Outline:
    prompt = PROMPT.replace("{{REDESIGN}}", proposal.model_dump_json(indent=2)).replace(
        "{{BRIEF}}", brief.model_dump_json(indent=2)
    )
    # MEDIUM: structuring a decision already made. The judgment happened upstream.
    return llm.generate_json(prompt, Outline, thinking="MEDIUM")


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    return {"outline": outline(state["redesign"], state["brief"])}
