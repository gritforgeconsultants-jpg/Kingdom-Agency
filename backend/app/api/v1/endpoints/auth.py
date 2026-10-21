from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthError, login_user, refresh_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        _, tokens = await register_user(
            db,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            organization_slug=body.organization_slug,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(**tokens)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        _, tokens = await login_user(db, email=body.email, password=body.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    try:
        tokens = await refresh_tokens(db, refresh_token=body.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def me(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user
