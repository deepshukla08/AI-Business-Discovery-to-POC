"""Deterministic work the agents rely on. No LLM calls in here.

    transcript.py  .txt / .vtt  -> chunks with speaker + timestamp
    whatsapp.py    chat export  -> chunks with sender + message number
    pdf.py         .pdf         -> chunks with page number
    website.py     url          -> fetched, stripped page text

Every parser returns the same shape, and every chunk carries a locator so the
brief can point back at the exact line it came from.
"""
