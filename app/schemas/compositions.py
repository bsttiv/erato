from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

STATUS = Literal["idea", "in_progress", "ready"]


class SectionsEnabled(BaseModel):
    chords: bool = True
    tablature: bool = False
    lyrics: bool = True
    demos: bool = True
    todos: bool = True


class CompositionCounts(BaseModel):
    chords: int = 0
    tabs: int = 0
    demos: int = 0
    todos_done: int = 0
    todos_total: int = 0


# Embedded Section Schemas
class ChordEntry(BaseModel):
    bar: int
    notes: List[int]
    name: str


class ChordsSection(BaseModel):
    instrument: str = "guitar"
    entries: List[ChordEntry] = []


class TabItem(BaseModel):
    id: str
    title: str = Field(..., min_length=1, max_length=80)
    strings: int = 6
    columns: List[Any] = []
    content: Optional[str] = None


class TablatureSection(BaseModel):
    strings: int = 6
    content: Optional[str] = ""
    tabs: List[TabItem] = []


class LyricsSection(BaseModel):
    content: str = ""


class SectionRevs(BaseModel):
    lyrics: int = 0
    chords: int = 0
    tablature: int = 0


class LyricsWriteResponse(LyricsSection):
    rev: int


class ChordsWriteResponse(ChordsSection):
    rev: int


class TablatureWriteResponse(TablatureSection):
    rev: int


class TodoItem(BaseModel):

    id: Optional[str] = None
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
    display_name: Optional[str] = None
    initials: Optional[str] = None


# Request Schemas
class CreateCompositionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    visibility: str = Field("private", pattern="^(public|private)$")
    key: Optional[str] = None
    bpm: Optional[int] = None
    time_signature: Optional[str] = None
    style_tags: List[str] = []
    status: STATUS = "idea"
    sections_enabled: SectionsEnabled = Field(default_factory=SectionsEnabled)


class UpdateCompositionRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    key: Optional[str] = None
    bpm: Optional[int] = None
    time_signature: Optional[str] = None
    style_tags: Optional[List[str]] = None
    status: Optional[STATUS] = None
    sections_enabled: Optional[SectionsEnabled] = None


class UpdateVisibilityRequest(BaseModel):
    visibility: str = Field(..., pattern="^(public|private)$")


class CreateInviteRequest(BaseModel):
    invited_email: Optional[str] = None
    role: str = Field("editor", pattern="^(editor|viewer)$")


class RedeemInviteRequest(BaseModel):
    token: str


# Response Schemas
class CompositionResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    visibility: str
    share_slug: Optional[str] = None
    key: Optional[str] = None
    bpm: Optional[int] = None
    time_signature: Optional[str] = None
    style_tags: List[str] = []
    status: STATUS = "idea"
    sections_enabled: SectionsEnabled = Field(default_factory=SectionsEnabled)
    user_role: Optional[str] = None
    section_revs: SectionRevs = Field(default_factory=SectionRevs)
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
    key: Optional[str] = None
    bpm: Optional[int] = None
    time_signature: Optional[str] = None
    style_tags: List[str] = []
    status: STATUS = "idea"
    sections_enabled: SectionsEnabled = Field(default_factory=SectionsEnabled)
    counts: CompositionCounts = Field(default_factory=CompositionCounts)
    chord_names: List[str] = []
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


class MemberDetail(BaseModel):
    user_id: Optional[str] = None
    invite_id: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None
    initials: Optional[str] = None
    role: str
    pending: bool = False
