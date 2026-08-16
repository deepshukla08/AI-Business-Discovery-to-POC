"""Agent 1 — one source in, cited findings out. The source may be a screenshot."""

from pathlib import Path

from app.agents import llm
from app.graph.state import DiscoveryState
from app.schemas.discovery import Chunk, Finding
from app.storage import store

PROMPT = (Path(__file__).parent / "prompts" / "extractor.md").read_text(encoding="utf-8")

MIME = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}


def render(chunks: list[Chunk]) -> str:
    lines = []
    for chunk in chunks:
        who = f" {chunk.speaker}:" if chunk.speaker else ""
        lines.append(f"[{chunk.id}] ({chunk.locator}){who} {chunk.text}")
    return "\n".join(lines)


def load_images(project_id: str, chunks: list[Chunk]) -> list[tuple[bytes, str]]:
    """Screenshots are handed to the model as pixels, not described into text first."""
    images = []
    for chunk in chunks:
        if not chunk.media:
            continue
        path = store.files_dir(project_id) / chunk.media
        images.append((path.read_bytes(), MIME.get(path.suffix.lower(), "image/jpeg")))
    return images


def extract(chunks: list[Chunk], project_id: str = "") -> list[Finding]:
    if not chunks:
        return []

    source_id = chunks[0].source_id
    prompt = PROMPT.replace("{{SOURCE}}", source_id).replace("{{CHUNKS}}", render(chunks))
    images = load_images(project_id, chunks) if project_id else []

    # LOW for text: mechanical — read a line, classify it, copy the id. Reading a
    # screenshot is genuinely harder, so it gets more room to think.
    findings: list[Finding] = (
        llm.generate_json(
            prompt,
            list[Finding],
            images=images,
            thinking="MEDIUM" if images else "LOW",
        )
        or []
    )

    # Rule 2 is enforced here, not just asked for in the prompt. A finding whose citations
    # are invented is indistinguishable from a hallucination, so it does not survive.
    real_ids = {chunk.id for chunk in chunks}
    kept = []
    for finding in findings:
        finding.cites = [cite for cite in finding.cites if cite in real_ids]
        finding.source_id = source_id
        if finding.cites:
            kept.append(finding)
    return kept


def run(state: DiscoveryState) -> dict:
    """LangGraph node."""
    # ponytail: one call per source. Fine at 400 chunks; batch by token count if a
    # client ever hands us a 4-hour transcript.
    return {"findings": extract(state["chunks"], state.get("project_id", ""))}
