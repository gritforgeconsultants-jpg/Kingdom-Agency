import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.child import AgeBand, AgentRank, AvatarChoice, ChildProfile, rank_for_xp
from app.models.consent import Consent
from app.models.user import User

PRIVACY_NOTICE_VERSION = "1.0"
PRIVACY_NOTICE_TEXT = """Kingdom Agency Privacy Notice for Parents/Guardians

What we collect about your child:
- A codename (not their real name) chosen by you
- An avatar selection
- An age band (7-8 or 9-11) — NOT their birthdate
- Mission completion records and points earned
- Optional short text entries ("field reports") they write

What we do NOT collect:
- Real names, last names, or birthdates
- Email addresses or passwords for children
- Photos, videos, or voice recordings from children
- Location data or device identifiers

How child data is used:
- Displayed only to you (parent) and your child's class leader
- Field reports require leader approval before any class visibility
- No child-to-child messaging or public profiles exist
- No third-party analytics, ads, or trackers are used

Your rights:
- Export all your child's data at any time
- Permanently delete all your child's data at any time
- Revoke consent at any time, which deactivates the child profile

This notice complies with COPPA (Children's Online Privacy Protection Act).
"""


def get_privacy_notice() -> dict[str, str]:
    return {"version": PRIVACY_NOTICE_VERSION, "text": PRIVACY_NOTICE_TEXT}


def _hash_consent_text() -> str:
    return hashlib.sha256(PRIVACY_NOTICE_TEXT.encode()).hexdigest()


async def create_child(
    db: AsyncSession,
    parent: User,
    codename: str,
    age_band: AgeBand,
    avatar: AvatarChoice = AvatarChoice.SHIELD,
) -> ChildProfile:
    child = ChildProfile(
        parent_id=parent.id,
        organization_id=parent.organization_id,
        codename=codename,
        avatar=avatar,
        age_band=age_band,
    )
    db.add(child)
    await db.flush()
    return child


async def grant_consent(
    db: AsyncSession,
    parent: User,
    child: ChildProfile,
    ip_address: str | None = None,
) -> Consent:
    consent = Consent(
        parent_id=parent.id,
        child_id=child.id,
        organization_id=parent.organization_id,
        consent_version=PRIVACY_NOTICE_VERSION,
        consent_text_hash=_hash_consent_text(),
        verification_method="pin_confirmation",
        ip_address=ip_address,
    )
    db.add(consent)
    await db.flush()
    return consent


async def list_children(db: AsyncSession, parent: User) -> list[ChildProfile]:
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.parent_id == parent.id,
            ChildProfile.organization_id == parent.organization_id,
            ChildProfile.is_active == True,  # noqa: E712
        )
    )
    return list(result.scalars().all())


async def get_child(
    db: AsyncSession, child_id: uuid.UUID, parent: User
) -> ChildProfile | None:
    result = await db.execute(
        select(ChildProfile).where(
            ChildProfile.id == child_id,
            ChildProfile.parent_id == parent.id,
            ChildProfile.organization_id == parent.organization_id,
        )
    )
    return result.scalar_one_or_none()


async def update_child(
    db: AsyncSession,
    child: ChildProfile,
    codename: str | None = None,
    avatar: AvatarChoice | None = None,
    age_band: AgeBand | None = None,
) -> ChildProfile:
    if codename is not None:
        child.codename = codename
    if avatar is not None:
        child.avatar = avatar
    if age_band is not None:
        child.age_band = age_band
    await db.flush()
    return child


async def export_child_data(
    db: AsyncSession, child: ChildProfile
) -> dict:
    consents_result = await db.execute(
        select(Consent).where(Consent.child_id == child.id)
    )
    consents = list(consents_result.scalars().all())

    return {
        "child": {
            "id": str(child.id),
            "codename": child.codename,
            "avatar": child.avatar.value,
            "age_band": child.age_band.value,
            "created_at": child.created_at.isoformat() if child.created_at else None,
        },
        "consents": [
            {
                "id": str(c.id),
                "version": c.consent_version,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
            }
            for c in consents
        ],
    }


async def delete_child_data(
    db: AsyncSession, child: ChildProfile
) -> None:
    await db.execute(
        Consent.__table__.delete().where(Consent.child_id == child.id)
    )
    await db.delete(child)
    await db.flush()


async def award_xp(
    db: AsyncSession,
    child: ChildProfile,
    amount: int,
) -> tuple[ChildProfile, AgentRank, AgentRank]:
    """Award XP and return (child, old_rank, new_rank). Caller checks for rank-up."""
    old_rank = rank_for_xp(child.xp)[0]
    child.xp += amount
    new_rank = rank_for_xp(child.xp)[0]
    await db.flush()
    return child, old_rank, new_rank


def create_kid_mode_token(parent: User, child: ChildProfile) -> str:
    return create_access_token({
        "sub": str(parent.id),
        "org": str(parent.organization_id),
        "role": parent.role.value,
        "kid_mode": True,
        "child_id": str(child.id),
    })


def verify_pin(parent: User, pin: str) -> bool:
    return parent.kid_mode_pin is not None and parent.kid_mode_pin == pin
