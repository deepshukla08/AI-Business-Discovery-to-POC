"""WhatsApp chat export: `11/03/2024, 9:41 am - Ravi Deshmukh: text`.

Two things people get wrong:
  - a wrapped message continues on the next line with no date prefix. Split on newlines
    and you shred every long message into fragments.
  - joins, adds and the encryption notice carry a date prefix but no `Sender:` — they
    look like messages and are not.
"""

import re

from app.schemas.discovery import Chunk
from app.tools.chunk import make_id

LINE = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\s*([ap]\.?m\.?)?\s*[-–]\s*(.*)$",
    re.IGNORECASE,
)


def parse(text: str, source_id: str, id_seed: str | None = None) -> list[Chunk]:
    seed = id_seed or source_id
    chunks: list[Chunk] = []

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            continue

        dated = LINE.match(line)
        if not dated:
            if chunks:  # wrapped continuation of the message above
                chunks[-1].text += " " + line.strip()
            continue

        date, clock, meridiem, body = dated.groups()
        sender, separator, message = body.partition(": ")
        if not separator:
            continue  # system line: created group, added someone, encryption notice

        chunks.append(
            Chunk(
                id=make_id(seed, len(chunks)),
                source_id=source_id,
                locator=f"{date} {clock}{' ' + meridiem if meridiem else ''}",
                speaker=sender.strip(),
                text=message.strip(),
            )
        )

    return [c for c in chunks if c.text]
