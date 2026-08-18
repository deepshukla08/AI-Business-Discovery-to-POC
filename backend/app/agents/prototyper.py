"""Agent 7 — the outline in, a clickable HTML demo out.

The one agent that returns code rather than structured data, so it is also the one that can
fail in a way the schema cannot catch. Everything it produces is checked before it is shown.
"""

import re
from pathlib import Path

from app.agents import llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Brief, Outline

PROMPT = (Path(__file__).parent / "prompts" / "prototyper.md").read_text(encoding="utf-8")

FENCE = re.compile(r"^\s*```(?:html)?\s*|\s*```\s*$", re.IGNORECASE)
# anything that would make the file depend on the network
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']\s*(?:https?:)?//""", re.IGNORECASE)


def strip_fence(html: str) -> str:
    """Models wrap code in ``` even when told not to. Cheaper to strip than to re-prompt."""
    return FENCE.sub("", html.strip())


def problems(html: str) -> list[str]:
    """What is wrong with this file, if anything. Empty list means it is usable."""
    found = []
    lowered = html.lower()

    if len(html) < 800:
        found.append(f"too short to be a real page ({len(html)} chars)")
    if "<html" not in lowered:
        found.append("no <html> element")
    if "</body>" not in lowered:
        found.append("truncated — no closing </body>")
    if "<script" not in lowered:
        found.append("no script, so nothing can be interactive")
    if EXTERNAL.search(html):
        found.append("pulls a resource from the network, so it will not work offline")
    return found


def build(outline: Outline, brief: Brief) -> tuple[str, list[str]]:
    prompt = PROMPT.replace("{{OUTLINE}}", outline.model_dump_json(indent=2)).replace(
        "{{BRIEF}}", brief.model_dump_json(indent=2)
    )
    # HIGH: writing working code is the hardest thing this pipeline does, and unlike the
    # other agents a plausible-looking wrong answer here is visibly broken.
    html = strip_fence(llm.generate_text(prompt, thinking="HIGH"))
    return html, problems(html)


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    html, faults = build(state["outline"], state["brief"])
    return {"prototype": html, "prototype_faults": faults}
