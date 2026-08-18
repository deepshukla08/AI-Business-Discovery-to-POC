"""Shapes crossing the HTTP boundary. Storage keeps plain dicts; these validate them."""

from typing import Literal

from pydantic import BaseModel

InputKind = Literal["transcript", "whatsapp", "document", "screenshot", "website", "notes"]


class NewProject(BaseModel):
    name: str
    client: str = ""


class TextInput(BaseModel):
    label: str
    content: str


class UrlInput(BaseModel):
    url: str


class ClientInput(BaseModel):
    id: str
    kind: InputKind
    source: Literal["file", "paste", "url"]
    label: str
    size: int
    added_at: str
    stored_as: str | None = None
    url: str | None = None


class Project(BaseModel):
    id: str
    name: str
    client: str
    created_at: str
    status: str
    inputs: list[ClientInput]
