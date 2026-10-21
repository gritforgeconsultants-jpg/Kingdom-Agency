from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.schemas.auth import OrganizationCreate, OrganizationResponse, UserResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    body: OrganizationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    """Create a new organization (field office). First user becomes admin."""
    existing = await db.execute(select(Organization).where(Organization.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Organization slug already taken")

    org = Organization(name=body.name, slug=body.slug, description=body.description)
    db.add(org)
    await db.flush()
    return org


@router.get("/mine", response_model=OrganizationResponse)
async def get_my_organization(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    result = await db.execute(
        select(Organization).where(Organization.id == user.organization_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.get("/mine/users", response_model=list[UserResponse])
async def list_org_users(
    user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[User]:
    """List users in the admin's org. Enforces tenant isolation."""
    result = await db.execute(
        select(User).where(User.organization_id == user.organization_id)
    )
    return list(result.scalars().all())


@router.put("/mine/users/{user_id}/role", response_model=UserResponse)
async def set_user_role(
    user_id: str,
    role: UserRole,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Admin promotes/demotes a user within their own org."""
    import uuid

    result = await db.execute(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.organization_id == admin.organization_id,
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found in your organization")
    target.role = role
    await db.flush()
    return target
