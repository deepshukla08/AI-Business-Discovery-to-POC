"""The two shapes the discovery pipeline is built on."""

from typing import Literal

from pydantic import BaseModel, Field

FindingType = Literal["fact", "pain", "requirement", "constraint", "question"]


class Chunk(BaseModel):
    """One citable piece of a source. The locator is what a citation points at."""

    id: str  # "a3f_012"
    source_id: str  # "call_1_kickoff.txt"
    locator: str  # "00:15:01" | "11/03/2024 9:41 am" | "p1 §3.1" | "image"
    speaker: str | None = None
    text: str
    # Set only for screenshots: the stored filename, so the model can be handed the
    # actual pixels and the UI can show them when the citation is clicked.
    media: str | None = None


class Finding(BaseModel):
    """One atomic thing the extractor noticed. Doubles as the model's output contract."""

    type: FindingType
    text: str = Field(description="One idea, stated flatly. Not a quote.")
    cites: list[str] = Field(description="Chunk ids this came from, copied exactly.")
    # filled in by us afterwards, not worth spending model tokens on
    source_id: str = ""


class Insight(BaseModel):
    """A finding after merging. The same point made in three files becomes one of these
    with three sources — and that count is the ranking signal."""

    type: FindingType
    text: str
    cites: list[str]
    sources: list[str]

    @property
    def corroboration(self) -> int:
        return len(self.sources)


class Cited(BaseModel):
    """A statement in the brief, with the chunks that back it."""

    text: str
    cites: list[str]


class Brief(BaseModel):
    """What a consultant would write up after reading everything."""

    goal: Cited = Field(description="What the client is actually trying to achieve.")
    current_process: list[Cited] = Field(description="How work happens today, in order.")
    pain_points: list[Cited] = Field(description="Most damaging first.")
    requirements: list[Cited]
    constraints: list[Cited]
    stated_wants: list[Cited] = Field(
        description="What the client asked for in their own words, kept separate from "
        "what the evidence says they need."
    )


ChangeKind = Literal["removed", "automated", "simplified", "new", "unchanged"]


class ProposedStep(BaseModel):
    step: str = Field(description="A step in the proposed way of working.")
    change: ChangeKind = Field(description="What happened to this step versus today.")
    why: str = Field(description="One line: what this fixes, or why it survives unchanged.")
    cites: list[str]


class Redesign(BaseModel):
    """A simpler way of working, anchored to the process that exists today."""

    summary: str = Field(description="The whole idea in one sentence a client would repeat.")
    to_be: list[ProposedStep]
    wins: list[Cited] = Field(description="Pain points this removes, and how.")
    not_solved: list[Cited] = Field(
        description="Pain points this does NOT fix. Being honest about the edges is "
        "worth more than pretending the proposal solves everything."
    )


class Role(BaseModel):
    name: str
    does: str = Field(description="What this person uses the system for.")


class Feature(BaseModel):
    name: str
    solves: str = Field(description="The specific pain this exists to remove.")
    priority: Literal["must", "should", "later"]


class Screen(BaseModel):
    name: str
    role: str = Field(description="Who opens this screen.")
    purpose: str
    elements: list[str] = Field(description="What is actually on it.")


class Outline(BaseModel):
    """The proposed application, concrete enough to build a prototype from."""

    app_name: str
    one_liner: str
    roles: list[Role]
    features: list[Feature]
    screens: list[Screen]
    flow: list[str] = Field(description="One pass through the system, start to finish.")


GapKind = Literal["unanswered", "contradiction", "never_discussed"]


class Gap(BaseModel):
    """Something the client has not told us, and we need before quoting the work."""

    kind: GapKind
    question: str = Field(description="The question to put to the client, as you'd ask it.")
    why_it_matters: str = Field(description="What goes wrong if we proceed without it.")
    cites: list[str] = Field(
        description="Chunks showing the question was dodged or the sources disagree. "
        "Empty is only valid for never_discussed."
    )
