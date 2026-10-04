from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel


class HistoryAuthor(BaseModel):
    id: str
    display_name: Optional[str] = None


class HistoryItemSummary(BaseModel):
    rev: int
    author: Optional[HistoryAuthor] = None
    created_at: datetime


class HistoryListResponse(BaseModel):
    items: List[HistoryItemSummary]
    next_before_rev: Optional[int] = None


class HistoryDetailResponse(BaseModel):
    rev: int
    content: Any
    author: Optional[HistoryAuthor] = None
    created_at: datetime
