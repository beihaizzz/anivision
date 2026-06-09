"""
Authentication Middleware

Provides FastAPI dependencies for JWT-based authentication:
- Extracts and validates Bearer tokens
- Loads the current user from the database
- Enforces active user status
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

# ── OAuth2 Scheme ─────────────────────────────────────────────────────
# FastAPI will automatically extract the Bearer token from the
# Authorization header and validate its format.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    description="JWT Bearer token obtained via /api/auth/login",
)


# ── Dependencies ──────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT token, then load the authenticated user.

    Raises HTTPException(401) if:
    - The token is invalid or expired
    - The user ID in the token does not exist in the database

    Returns the authenticated User ORM instance.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Load user from database
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that additionally checks if the user account is active.

    Raises HTTPException(403) if the user's account is deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user
