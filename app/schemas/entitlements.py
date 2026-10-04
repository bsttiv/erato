from typing import Literal, Optional
from pydantic import BaseModel


class EntitlementsResponse(BaseModel):
    can_share_with_people: bool
    can_create_band: bool
    can_view_history: bool
    demo_limit_per_composition: Optional[int] = None
    extensions_available: bool
    band_creation_mode: Literal["direct", "hand_off"]
