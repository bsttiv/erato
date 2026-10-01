from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UploadSignatureResponse(BaseModel):
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    resource_type: str = "video"
    type: str = "authenticated"
    tags: str = "pending"


class CreateDemoRequest(BaseModel):
    public_id: str
    version: str
    signature: str
    title: str = Field(..., min_length=1, max_length=150)
    duration_s: float = Field(..., ge=0)


class DemoResponse(BaseModel):
    demo_id: str
    cloudinary_public_id: str
    title: str
    duration_s: float
    uploaded_by: str
    uploaded_at: datetime


class DemoUrlResponse(BaseModel):
    url: str
    expires_at: int


class CreateCommentRequest(BaseModel):
    timestamp_s: float = Field(..., ge=0)
    text: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: str
    composition_id: str
    demo_id: str
    author_id: str
    timestamp_s: float
    text: str
    created_at: datetime
