"""
Post & Comment Schemas

Request and response models for community posts and threaded comments.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserBrief(BaseModel):
    """Lightweight user reference for nested responses (avoids exposing email)."""

    id: int
    username: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class PostCreate(BaseModel):
    """Request model for creating a new post."""

    content: str = Field(
        ..., min_length=1, description="Post text content (min 1 char after strip)"
    )
    image_urls: list[str] = Field(
        default_factory=list, description="Optional image URLs"
    )
    tags: list[str] = Field(
        default_factory=list, description="Optional tags"
    )

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v: str) -> str:
        """Strip whitespace from content before validation."""
        if isinstance(v, str):
            return v.strip()
        return v


class PostResponse(BaseModel):
    """Response model for a single post."""

    id: int
    content: str
    image_urls: list[str]
    tags: list[str]
    like_count: int = 0
    comment_count: int = 0
    user: UserBrief
    created_at: datetime

    model_config = {"from_attributes": True}


class PostUpdateRequest(BaseModel):
    """Request model for partial post update (all fields optional)."""

    content: Optional[str] = None
    tags: Optional[list[str]] = None


class CommentCreate(BaseModel):
    """Request model for creating a comment (top-level or reply)."""

    content: str = Field(
        ..., min_length=1, description="Comment text content (min 1 char after strip)"
    )
    parent_id: Optional[int] = Field(
        default=None, description="Parent comment ID for nested replies"
    )

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v: str) -> str:
        """Strip whitespace from content before validation."""
        if isinstance(v, str):
            return v.strip()
        return v


class CommentResponse(BaseModel):
    """Response model for a single comment with optional nested replies."""

    id: int
    content: str
    user: UserBrief
    parent_id: Optional[int] = None
    replies: list["CommentResponse"] = Field(
        default_factory=list, description="Nested reply comments"
    )
    created_at: datetime

    model_config = {"from_attributes": True}


# Resolve forward reference for self-referential CommentResponse
CommentResponse.model_rebuild()


class PostListResponse(BaseModel):
    """Paginated list of posts."""

    items: list[PostResponse]
    total: int
    page: int
    size: int


class CommentListResponse(BaseModel):
    """Paginated list of comments."""

    items: list[CommentResponse]
    total: int
    page: int
    size: int
