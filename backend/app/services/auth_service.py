"""
Auth Service

Business logic for user authentication:
- Registration with duplicate checking
- Credential verification
- JWT token generation
"""

from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.utils.security import create_access_token, get_password_hash, verify_password


async def register_user(
    db: AsyncSession,
    user_data: RegisterRequest,
) -> User:
    """
    Register a new user account.

    Validates that the username and email are unique, hashes the password,
    and persists the new user to the database.

    Args:
        db: Database session.
        user_data: Validated registration request data.

    Returns:
        The newly created User instance.

    Raises:
        HTTPException(409): If username or email already exists.
    """
    # Check for existing username or email
    existing = await db.execute(
        select(User).where(
            or_(User.username == user_data.username, User.email == user_data.email)
        )
    )
    existing_user = existing.scalar_one_or_none()
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    # Create user with hashed password
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role="user",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> Optional[User]:
    """
    Authenticate a user by username/email and password.

    Supports login with either username or email as the credential.

    Args:
        db: Database session.
        username: Username or email provided by the user.
        password: Plaintext password.

    Returns:
        The authenticated User instance, or None if credentials are invalid.
    """
    # Allow login with either username or email
    result = await db.execute(
        select(User).where(
            or_(User.username == username, User.email == username)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_user_token(user: User) -> dict:
    """
    Generate a JWT access token and build the token response payload.

    Args:
        user: The authenticated User instance.

    Returns:
        Dictionary ready to construct TokenResponse.
    """
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "bio": user.bio or "",
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }
