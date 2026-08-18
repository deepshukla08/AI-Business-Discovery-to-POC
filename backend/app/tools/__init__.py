"""Deterministic work the agents rely on. No model calls in here, ever.

    ingest.py      picks a parser by sniffing the content, not the filename
    transcript.py  [00:15:01] Speaker: text   -> chunk per utterance
    whatsapp.py    11/03/2024, 9:41 am - X: y -> chunk per message
    pdf.py         .pdf                       -> chunk per numbered clause
    plain.py       pasted prose               -> chunk per paragraph
    chunk.py       chunk ids: unique per source, stable across re-runs

Every parser returns the same shape, and every chunk carries a locator — a timestamp, a
message time, a clause number — so a finding can point back at the exact line it came
from. The chunk boundary decides how precise a citation can ever be.

Images are not parsed: an image cannot be split, so ingest emits one chunk carrying the
file, and the extractor hands the pixels to the model.
"""
