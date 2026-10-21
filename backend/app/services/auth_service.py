import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import User, UserRole


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


async def register_user(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
    organization_slug: str,
) -> tuple[User, dict[str, str]]:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise AuthError("Email already registered", 409)

    org = await db.execute(
        select(Organization).where(Organization.slug == organization_slug)
    )
    organization = org.scalar_one_or_none()
    if not organization:
        raise AuthError("Organization not found", 404)

    user = User(
        email=email,
        hashed_password=hash_password(password),
        display_name=display_name,
        role=UserRole.PARENT,
        organization_id=organization.id,
    )
    db.add(user)
    await db.flush()

    tokens = _create_tokens(user)
    return user, tokens


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, dict[str, str]]:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password", 401)

    if not user.is_active:
        raise AuthError("Account is deactivated", 403)

    tokens = _create_tokens(user)
    return user, tokens


async def refresh_tokens(
    db: AsyncSession,
    refresh_token: str,
) -> dict[str, str]:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise AuthError("Invalid refresh token", 401)

    user_id = payload.get("sub")
    if not user_id:
        raise AuthError("Invalid refresh token", 401)

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthError("User not found or inactive", 401)

    return _create_tokens(user)


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


def _create_tokens(user: User) -> dict[str, str]:
    token_data = {
        "sub": str(user.id),
        "org": str(user.organization_id),
        "role": user.role.value,
    }
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }
