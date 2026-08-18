"""Meeting transcripts: `[00:15:01] Ravi Deshmukh: text`.

Three kinds of line, and the third is the one people get wrong:
  - a timestamped utterance          -> its own chunk
  - a bracketed editor note          -> its own chunk, no speaker
  - anything else                    -> a wrapped continuation of the line above
"""

import re

from app.schemas.discovery import Chunk
from app.tools.chunk import make_id

UTTERANCE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s*([^:]{1,60}?):\s*(.*)$")


def parse(text: str, source_id: str, id_seed: str | None = None) -> list[Chunk]:
    seed = id_seed or source_id
    lines = text.splitlines()
    first = next((i for i, line in enumerate(lines) if line.startswith("[")), len(lines))

    chunks: list[Chunk] = []

    def add(locator: str, speaker: str | None, body: str) -> None:
        chunks.append(
            Chunk(
                id=make_id(seed, len(chunks)),
                source_id=source_id,
                locator=locator,
                speaker=speaker,
                text=body.strip(),
            )
        )

    # everything above the first timestamp is the header block: date, participants
    header = " ".join(line.strip() for line in lines[:first] if line.strip())
    if header:
        add("header", None, header)

    for raw in lines[first:]:
        line = raw.strip()
        if not line:
            continue

        spoken = UTTERANCE.match(line)
        if spoken:
            timestamp, speaker, said = spoken.groups()
            add(timestamp, speaker.strip(), said)
        elif line.startswith("["):
            add("note", None, line.strip("[]"))
        elif chunks:
            # wrapped line — belongs to whatever came before it
            chunks[-1].text += " " + line

    return [c for c in chunks if c.text]
