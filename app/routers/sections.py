from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.permissions import Action
from app.deps import AuthContext, require
from app.schemas.compositions import (
    ChordsSection,
    ChordsWriteResponse,
    LyricsSection,
    LyricsWriteResponse,
    TablatureSection,
    TablatureWriteResponse,
    TodoItem,
)
from app.services.composition_service import CompositionService
from app.services.versioning_service import VersioningService

router = APIRouter(prefix="/api/compositions/{composition_id}", tags=["sections"])


def get_service() -> CompositionService:
    return CompositionService()


def get_versioning_service() -> VersioningService:
    return VersioningService()


# Chords
@router.get("/chords", response_model=ChordsSection, status_code=status.HTTP_200_OK)
async def get_chords(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("chords") or ChordsSection()


@router.put("/chords", response_model=ChordsWriteResponse, status_code=status.HTTP_200_OK)
async def update_chords(
    composition_id: str,
    body: ChordsSection,
    expected_rev: Optional[int] = Query(None, ge=0),
    auth: AuthContext = Depends(require(Action.EDIT)),
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    author_id = auth.user["id"] if auth.user else str(auth.composition.get("owner_id"))
    content, new_rev = await versioning_service.update_versioned_section(
        composition_id=composition_id,
        section_name="chords",
        content=body.model_dump(),
        author_id=author_id,
        expected_rev=expected_rev,
    )
    return ChordsWriteResponse(**content, rev=new_rev)


# Tablature
@router.get("/tablature", response_model=TablatureSection, status_code=status.HTTP_200_OK)
async def get_tablature(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("tablature") or TablatureSection()


@router.put("/tablature", response_model=TablatureWriteResponse, status_code=status.HTTP_200_OK)
async def update_tablature(
    composition_id: str,
    body: TablatureSection,
    expected_rev: Optional[int] = Query(None, ge=0),
    auth: AuthContext = Depends(require(Action.EDIT)),
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    author_id = auth.user["id"] if auth.user else str(auth.composition.get("owner_id"))
    content, new_rev = await versioning_service.update_versioned_section(
        composition_id=composition_id,
        section_name="tablature",
        content=body.model_dump(),
        author_id=author_id,
        expected_rev=expected_rev,
    )
    return TablatureWriteResponse(**content, rev=new_rev)


# Lyrics
@router.get("/lyrics", response_model=LyricsSection, status_code=status.HTTP_200_OK)
async def get_lyrics(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("lyrics") or LyricsSection()


@router.put("/lyrics", response_model=LyricsWriteResponse, status_code=status.HTTP_200_OK)
async def update_lyrics(
    composition_id: str,
    body: LyricsSection,
    expected_rev: Optional[int] = Query(None, ge=0),
    auth: AuthContext = Depends(require(Action.EDIT)),
    versioning_service: VersioningService = Depends(get_versioning_service),
) -> Any:
    author_id = auth.user["id"] if auth.user else str(auth.composition.get("owner_id"))
    content, new_rev = await versioning_service.update_versioned_section(
        composition_id=composition_id,
        section_name="lyrics",
        content=body.model_dump(),
        author_id=author_id,
        expected_rev=expected_rev,
    )
    return LyricsWriteResponse(**content, rev=new_rev)



# Todos
@router.get("/todos", response_model=List[TodoItem], status_code=status.HTTP_200_OK)
async def get_todos(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("todos") or []


@router.put("/todos", response_model=List[TodoItem], status_code=status.HTTP_200_OK)
async def update_todos(
    composition_id: str,
    body: List[TodoItem],
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: CompositionService = Depends(get_service),
) -> Any:
    updated = await service.update_section(
        composition_id,
        "todos",
        [item.model_dump() for item in body],
    )
    return updated.get("todos") or []
