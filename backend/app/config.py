"""Everything environment-dependent lives here. One place to look."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Windows consoles default to cp1252. Our sample WhatsApp export contains emoji, so a
# trace line quoting one would raise UnicodeEncodeError mid-stream and kill the run.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Dev only. A deployment would read allowed origins from the environment.
FRONTEND_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Confirmed available on this key via client.models.list(). Flash handles the whole
# pipeline; move a single node to a pro model only if its output quality forces it.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
# The free tier allows 20 requests/day PER MODEL, and the newest model is also the busiest
# (503s under load). Each entry here is a separate daily allowance, so the chain is both a
# reliability measure and a budget one. Full flash models first, lite variants last —
# they are cheaper and less capable, so they are a fallback, not a default.
# Aliases like gemini-flash-latest are deliberately absent: they share the quota of
# whatever they point at, so they add no capacity.
GEMINI_FALLBACKS = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]
