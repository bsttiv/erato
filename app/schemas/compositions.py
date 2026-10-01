from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


# Embedded Section Schemas
class ChordEntry(BaseModel):
    bar: int
    notes: List[int]
    name: str


class ChordsSection(BaseModel):
    instrument: str = "guitar"
    entries: List[ChordEntry] = []


class TablatureSection(BaseModel):
    strings: int = 6
    content: str = ""


class LyricsSection(BaseModel):
    content: str = ""


class TodoItem(BaseModel):
    text: str
    done: bool = False


class DemoItem(BaseModel):
    demo_id: str
    cloudinary_public_id: str
    title: str
    duration_s: float
    uploaded_by: str
    uploaded_at: datetime


class MemberItem(BaseModel):
    user_id: str
    role: str = "editor"


# Request Schemas
class CreateCompositionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    visibility: str = Field("private", pattern="^(public|private)$")


class UpdateCompositionRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)


class UpdateVisibilityRequest(BaseModel):
    visibility: str = Field(..., pattern="^(public|private)$")


class CreateInviteRequest(BaseModel):
    invited_email: Optional[str] = None
    role: str = Field("editor", pattern="^(editor)$")


class RedeemInviteRequest(BaseModel):
    token: str


# Response Schemas
class CompositionResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    visibility: str
    share_slug: Optional[str] = None
    chords: Optional[ChordsSection] = None
    tablature: Optional[TablatureSection] = None
    lyrics: Optional[LyricsSection] = None
    todos: List[TodoItem] = []
    demos: List[DemoItem] = []
    members: List[MemberItem] = []
    created_at: datetime
    updated_at: datetime


class CompositionListItem(BaseModel):
    id: str
    owner_id: str
    title: str
    visibility: str
    created_at: datetime
    updated_at: datetime


class InviteResponse(BaseModel):
    id: str
    composition_id: str
    invite_url: Optional[str] = None
    invited_email: Optional[str] = None
    role: str
    expires_at: datetime
    used_at: Optional[datetime] = None
