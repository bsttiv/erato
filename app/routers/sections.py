from typing import Any, List
from fastapi import APIRouter, Depends, status

from app.core.permissions import Action
from app.deps import AuthContext, require
from app.schemas.compositions import (
    ChordsSection,
    LyricsSection,
    TablatureSection,
    TodoItem,
)
from app.services.composition_service import CompositionService

router = APIRouter(prefix="/api/compositions/{composition_id}", tags=["sections"])


def get_service() -> CompositionService:
    return CompositionService()


# Chords
@router.get("/chords", response_model=ChordsSection, status_code=status.HTTP_200_OK)
async def get_chords(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("chords") or ChordsSection()


@router.put("/chords", response_model=ChordsSection, status_code=status.HTTP_200_OK)
async def update_chords(
    composition_id: str,
    body: ChordsSection,
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: CompositionService = Depends(get_service),
) -> Any:
    updated = await service.update_section(composition_id, "chords", body.model_dump())
    return updated.get("chords") or ChordsSection()


# Tablature
@router.get("/tablature", response_model=TablatureSection, status_code=status.HTTP_200_OK)
async def get_tablature(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("tablature") or TablatureSection()


@router.put("/tablature", response_model=TablatureSection, status_code=status.HTTP_200_OK)
async def update_tablature(
    composition_id: str,
    body: TablatureSection,
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: CompositionService = Depends(get_service),
) -> Any:
    updated = await service.update_section(composition_id, "tablature", body.model_dump())
    return updated.get("tablature") or TablatureSection()


# Lyrics
@router.get("/lyrics", response_model=LyricsSection, status_code=status.HTTP_200_OK)
async def get_lyrics(
    composition_id: str,
    auth: AuthContext = Depends(require(Action.VIEW)),
) -> Any:
    return auth.composition.get("lyrics") or LyricsSection()


@router.put("/lyrics", response_model=LyricsSection, status_code=status.HTTP_200_OK)
async def update_lyrics(
    composition_id: str,
    body: LyricsSection,
    auth: AuthContext = Depends(require(Action.EDIT)),
    service: CompositionService = Depends(get_service),
) -> Any:
    updated = await service.update_section(composition_id, "lyrics", body.model_dump())
    return updated.get("lyrics") or LyricsSection()


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
