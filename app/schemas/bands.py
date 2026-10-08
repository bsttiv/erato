from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints

BandRole = Literal['owner', 'member']
BandName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class BandCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: BandName


class BandRename(BandCreate):
    pass


class BandMember(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    initials: Optional[str] = None
    role: BandRole


class PendingTransfer(BaseModel):
    to_user_id: str
    requested_at: datetime
    expires_at: datetime


class BandSummary(BaseModel):
    id: str
    name: str
    owner_id: str
    user_role: BandRole
    seats_used: int
    seat_limit: Optional[int]
    active: bool


class BandResponse(BandSummary):
    members: list[BandMember]
    pending_transfer: Optional[PendingTransfer]
    created_at: datetime
    updated_at: datetime


class BandInviteCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')


class BandInviteSummary(BaseModel):
    id: str
    expires_at: datetime


class BandInviteResponse(BandInviteSummary):
    invite_url: str
