"""
Common Pydantic Schemas

Shared request/response models used across multiple API endpoints.
"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, conint

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
    )
    size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T] = Field(description="List of items for the current page")
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")

    @property
    def pages(self) -> int:
        """Calculate the total number of pages."""
        if self.size == 0:
            return 0
        return (self.total + self.size - 1) // self.size

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Simple message response for status endpoints."""

    message: str
    detail: Optional[str] = None
