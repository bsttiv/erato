from typing import List
from fastapi import APIRouter, Depends, status

from app.core.permissions import Action
from app.deps import AuthContext, current_user_required, require
from app.schemas.demos import (

    CommentResponse,
    CreateCommentRequest,
    CreateDemoRequest,
    DemoResponse,
    DemoUrlResponse,
    UploadSignatureResponse,
)
from app.services.demo_service import DemoService

router = APIRouter(prefix="/api/compositions/{composition_id}/demos", tags=["demos"])


def get_service() -> DemoService:
    return DemoService()


@router.post(
    "/upload-signature",
    response_model=UploadSignatureResponse,
    status_code=status.HTTP_200_OK,
)
async def request_upload_signature(
    composition_id: str,
    current_user: dict = Depends(current_user_required),
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: DemoService = Depends(get_service),
) -> UploadSignatureResponse:
    """Issue a signed Cloudinary upload credential without receiving file bytes."""
    sig_params = service.get_upload_signature(composition_id)
    return UploadSignatureResponse(**sig_params)



@router.post(
    "",
    response_model=DemoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def confirm_demo(
    composition_id: str,
    body: CreateDemoRequest,
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: DemoService = Depends(get_service),
) -> DemoResponse:
    """Verify Cloudinary result signature and register the demo reference."""
    uploader_id = auth.user["id"] if auth.user else str(auth.composition["owner_id"])
    demo = await service.confirm_upload(
        composition_id=composition_id,
        uploader_id=uploader_id,
        public_id=body.public_id,
        version=body.version,
        signature=body.signature,
        title=body.title,
        duration_s=body.duration_s,
    )
    return DemoResponse(
        demo_id=demo["demo_id"],
        cloudinary_public_id=demo["cloudinary_public_id"],
        title=demo["title"],
        duration_s=demo["duration_s"],
        uploaded_by=str(demo["uploaded_by"]),
        uploaded_at=demo["uploaded_at"],
    )


@router.get(
    "/{demo_id}/url",
    response_model=DemoUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def get_demo_playback_url(
    composition_id: str,
    demo_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
    service: DemoService = Depends(get_service),
) -> DemoUrlResponse:
    """Mint short-lived signed delivery URL for playback without transformations."""
    url_data = await service.mint_playback_url(composition_id, demo_id)
    return DemoUrlResponse(**url_data)


@router.post(
    "/{demo_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_demo_comment(
    composition_id: str,
    demo_id: str,
    body: CreateCommentRequest,
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: DemoService = Depends(get_service),
) -> CommentResponse:
    """Record a timestamp-anchored comment on a demo (editor or owner)."""
    author_id = auth.user["id"] if auth.user else str(auth.composition["owner_id"])
    comment = await service.add_comment(
        composition_id=composition_id,
        demo_id=demo_id,
        author_id=author_id,
        timestamp_s=body.timestamp_s,
        text=body.text,
    )
    return CommentResponse(
        id=str(comment["_id"]),
        composition_id=str(comment["composition_id"]),
        demo_id=comment["demo_id"],
        author_id=str(comment["author_id"]),
        timestamp_s=comment["timestamp_s"],
        text=comment["text"],
        created_at=comment["created_at"],
    )


@router.get(
    "/{demo_id}/comments",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
)
async def list_demo_comments(
    composition_id: str,
    demo_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
    service: DemoService = Depends(get_service),
) -> List[CommentResponse]:
    """List timestamped comments for a demo, requiring view permission."""
    docs = await service.list_comments(composition_id, demo_id)
    return [
        CommentResponse(
            id=str(c["_id"]),
            composition_id=str(c["composition_id"]),
            demo_id=c["demo_id"],
            author_id=str(c["author_id"]),
            timestamp_s=c["timestamp_s"],
            text=c["text"],
            created_at=c["created_at"],
        )
        for c in docs
    ]
