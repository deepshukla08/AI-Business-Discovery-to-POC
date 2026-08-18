"""Pasted notes and anything without structure: one chunk per paragraph."""

import re

from app.schemas.discovery import Chunk
from app.tools.chunk import make_id

PARAGRAPH = re.compile(r"\n\s*\n")


def parse(text: str, source_id: str, id_seed: str | None = None) -> list[Chunk]:
    seed = id_seed or source_id
    paragraphs = [p.strip() for p in PARAGRAPH.split(text) if p.strip()]
    return [
        Chunk(
            id=make_id(seed, i),
            source_id=source_id,
            locator=f"para {i + 1}",
            text=paragraph,
        )
        for i, paragraph in enumerate(paragraphs)
    ]
