"""
Routers Package

API route modules organized by domain.
"""

from app.routers import (
    analytics,
    auth,
    characters,
    posts,
    recognition,
    search,
    users,
)

__all__ = [
    "analytics",
    "auth",
    "characters",
    "posts",
    "recognition",
    "search",
    "users",
]
