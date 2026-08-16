"""PDFs, chunked by numbered clause rather than by page.

Extracted PDF text has no blank lines and wraps mid-sentence, so paragraphs have to be
rebuilt. A numbered clause (`3.1 ...`) starts a new one; everything else continues the
previous. The payoff is a citation that reads `p1 §3.1` instead of the useless "page 1".
"""

import re
from pathlib import Path

from pypdf import PdfReader

from app.schemas.discovery import Chunk
from app.tools.chunk import make_id

CLAUSE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+\S")


def parse(path: Path, source_id: str, id_seed: str | None = None) -> list[Chunk]:
    seed = id_seed or source_id
    blocks: list[tuple[str, list[str]]] = []

    for page_number, page in enumerate(PdfReader(path).pages, start=1):
        for raw in (page.extract_text() or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            numbered = CLAUSE.match(line)
            if numbered:
                blocks.append((f"p{page_number} §{numbered.group(1)}", [line]))
            elif blocks:
                # a clause that runs over a page break keeps flowing into the same
                # block — starting a fresh one per page would cut sentences in half
                blocks[-1][1].append(line)
            else:
                blocks.append((f"p{page_number}", [line]))  # front matter

    chunks: list[Chunk] = []
    for locator, lines in blocks:
        text = " ".join(lines).strip()
        if not text:
            continue
        chunks.append(
            Chunk(
                id=make_id(seed, len(chunks)),
                source_id=source_id,
                locator=locator,
                text=text,
            )
        )
    return chunks
