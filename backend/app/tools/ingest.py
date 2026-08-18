"""Picks the right parser for a stored input.

Routing is by content first, filename second — someone who exports a WhatsApp chat and
saves it as `chat.txt` should still get the WhatsApp parser.

Returns (chunks, skip_reason). A skip reason is not an error — it is how the UI shows you
honestly that a parser has not been built yet.
"""

import re

from app.schemas.discovery import Chunk
from app.storage import store
from app.tools import pdf, plain, transcript, whatsapp
from app.tools.chunk import make_id

TIMESTAMPED = re.compile(r"^\[\d{2}:\d{2}:\d{2}\]", re.MULTILINE)
CHAT_EXPORT = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}", re.MULTILINE)
TEXTUAL = {".txt", ".vtt", ".md", ".log"}
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def parse_input(pid: str, record: dict) -> tuple[list[Chunk], str | None]:
    stored_as = record.get("stored_as")
    if not stored_as:
        return [], "nothing stored for this input"

    path = store.files_dir(pid) / stored_as
    if not path.exists():
        return [], "file missing on disk"

    label, seed = record["label"], record["id"]
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return pdf.parse(path, label, id_seed=seed), None

    if suffix in IMAGES:
        # An image cannot be split, so it is one chunk: the picture itself. Findings
        # cite it like any other, and clicking that citation shows the screenshot.
        return [
            Chunk(
                id=make_id(seed, 0),
                source_id=label,
                locator="image",
                text=f"[screenshot: {label}]",
                media=stored_as,
            )
        ], None

    if suffix in TEXTUAL or record["kind"] in ("transcript", "notes", "whatsapp"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if CHAT_EXPORT.search(text):
            parser = whatsapp
        elif TIMESTAMPED.search(text):
            parser = transcript
        else:
            parser = plain
        return parser.parse(text, label, id_seed=seed), None

    return [], f"no parser for '{record['kind']}' yet"
