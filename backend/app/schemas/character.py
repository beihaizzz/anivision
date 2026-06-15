"""
Character & Work Schemas

Defines Pydantic models for character and work API responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import PaginatedResponse


class WorkResponse(BaseModel):
    """Work (anime/manga/game) response returned by the API."""

    id: int
    title: str
    title_jp: Optional[str] = None
    type: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterResponse(BaseModel):
    """Character response returned by the API."""

    id: int
    name: str
    name_jp: Optional[str] = None
    aliases: list[str] = []
    description: Optional[str] = ""
    image_url: Optional[str] = None
    work: Optional[WorkResponse] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CharacterListResponse(PaginatedResponse[CharacterResponse]):
    """Paginated list of characters."""
    pass


class WorkListResponse(PaginatedResponse[WorkResponse]):
    """Paginated list of works."""
    pass


class CharacterFilterParams(BaseModel):
    """Optional query parameters for filtering characters."""

    name: Optional[str] = None
    work_id: Optional[int] = None
