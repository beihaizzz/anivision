"""
Behavior Logging Middleware

Asynchronously logs user actions (searches, views, etc.) to the database
using asyncio.create_task to avoid blocking the request response.
Skips health check, docs, and static file requests.

Path-to-action mapping determines the action_type stored in the log.
"""

import asyncio
import re
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import AsyncSessionLocal
from app.models.behavior_log import BehaviorLog

# ── Excluded Paths ────────────────────────────────────────────────────
# These paths will NOT generate behavior log entries.

EXCLUDED_PATHS = {
    "/api/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
}

# ── Path-to-Action Mapping ─────────────────────────────────────────────
# Regex patterns matched against request path to infer action_type.
# Patterns are evaluated in order; first match wins.

PATH_ACTION_MAP: list[tuple[str, str]] = [
    (r"^/api/search", "search"),
    (r"^/api/posts", "view_posts"),
    (r"^/api/characters", "view_characters"),
    (r"^/api/recognition/upload", "recognition_upload"),
    (r"^/api/recognition/history", "view_history"),
    (r"^/api/users/\d+$", "view_profile"),
    (r"^/api/analytics", "view_analytics"),
]


def _infer_action_type(path: str) -> str:
    """Infer the action type from the request path using regex patterns."""
    for pattern, action in PATH_ACTION_MAP:
        if re.match(pattern, path):
            return action
    return "other"


# ══════════════════════════════════════════════════════════════════════════
# Middleware
# ══════════════════════════════════════════════════════════════════════════


class BehaviorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs user behavior to the database asynchronously.

    Uses asyncio.create_task to fire-and-forget the database write,
    ensuring the main request response is never blocked by logging I/O.
    Silently catches all exceptions — logging failures must never break
    the application.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip excluded paths entirely
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        # Process the actual request first
        response = await call_next(request)

        # ── Extract request metadata ──
        # User context (set by auth middleware for authenticated requests)
        user_id: Optional[int] = None
        if hasattr(request.state, "user") and request.state.user is not None:
            user_id = getattr(request.state.user, "id", None)

        action_type = _infer_action_type(path)

        # Fire-and-forget: schedule the DB write without blocking the response
        asyncio.create_task(
            _log_behavior(
                user_id=user_id,
                action_type=action_type,
                path=path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        )

        return response


# ══════════════════════════════════════════════════════════════════════════
# Logging Function
# ══════════════════════════════════════════════════════════════════════════


async def _log_behavior(
    user_id: Optional[int],
    action_type: str,
    path: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Write a behavior log entry to the database.

    All exceptions are silently caught. Behavior logging is best-effort;
    it must never cause a request to fail or a response to be delayed.
    """
    try:
        async with AsyncSessionLocal() as db:
            log_entry = BehaviorLog(
                user_id=user_id,
                action_type=action_type,
                context={"path": path},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(log_entry)
            await db.commit()
    except Exception:
        pass  # Best-effort: never let logging failures propagate
