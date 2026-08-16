"""What flows between nodes."""

import operator
from typing import Annotated, TypedDict

from app.schemas.discovery import (
    Answer,
    Brief,
    Chunk,
    Finding,
    Gap,
    Insight,
    Outline,
    Redesign,
)


class DiscoveryState(TypedDict, total=False):
    project_id: str
    chunks: list[Chunk]

    # operator.add matters: one extractor runs per source, in parallel. Without a
    # reducer the last node to finish silently overwrites the others' findings.
    findings: Annotated[list[Finding], operator.add]

    # everything below has exactly one writer, so no reducer is needed
    insights: list[Insight]
    brief: Brief
    gaps: list[Gap]
    answers: list[Answer]
    redesign: Redesign
    outline: Outline

    # the prototype is a whole HTML file, not a record — kept out of run.json and
    # written to its own file so the run result stays readable
    prototype: str
    prototype_faults: list[str]
