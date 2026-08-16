"""Chunk ids.

Deterministic and unique across sources, so a citation stays valid across re-runs and
two files can never produce the same id.
"""

import hashlib


def make_id(seed: str, index: int) -> str:
    """`seed` must be unique per source — two files both named notes.txt would
    otherwise mint the same chunk ids and every citation between them would be a lie."""
    return f"{hashlib.sha1(seed.encode()).hexdigest()[:3]}_{index:03d}"
