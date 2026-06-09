"""
Auth Router

Authentication endpoints:
- POST /api/auth/register  — Create new account
- POST /api/auth/login     — Authenticate and get JWT
- GET  /api/auth/me        — Get current user profile
- PUT  /api/auth/me        — Update current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_user_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Registration ──────────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new user account.

    - **username**: 3-50 characters, letters/digits/underscores only
    - **email**: Valid email address
    - **password**: At least 8 characters with uppercase, lowercase, and digit
    """
    user = await register_user(db, request)
    return UserResponse.model_validate(user)


# ── Login ─────────────────────────────────────────────────────────────


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and receive JWT token",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with username/email and password.

    Returns a JWT access token valid for 24 hours (configurable).
    Use the token in the `Authorization: Bearer <token>` header
    for authenticated endpoints.
    """
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token_data = await create_user_token(user)
    return TokenResponse(**token_data)


# ── Current User Profile ──────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Returns the profile of the currently authenticated user.

    Requires a valid JWT Bearer token.
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
)
async def update_me(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update the authenticated user's bio and/or avatar URL.

    Only the provided fields will be updated.
    Requires a valid JWT Bearer token.
    """
    if request.bio is not None:
        current_user.bio = request.bio
    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url

    await db.flush()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
