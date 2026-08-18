"""The rule every agent is held to, enforced in code rather than trusted to the prompt.

A citation the model invented is indistinguishable from a hallucinated claim, so invented
ids are stripped and anything left without support is dropped.
"""

from typing import TypeVar

T = TypeVar("T")


def enforce(items: list[T], valid_ids: set[str], *, allow_uncited: bool = False) -> list[T]:
    """Strip citations that point at nothing. Drop items left with none."""
    kept = []
    for item in items:
        item.cites = [cite for cite in item.cites if cite in valid_ids]
        if item.cites or allow_uncited:
            kept.append(item)
    return kept
