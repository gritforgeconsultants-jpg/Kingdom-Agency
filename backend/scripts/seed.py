"""Seed script: creates Beacon field office, an admin, a leader, and a parent."""

import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory, engine
from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User, UserRole


async def seed() -> None:
    async with async_session_factory() as db:
        existing = await db.execute(select(Organization).where(Organization.slug == "beacon"))
        if existing.scalar_one_or_none():
            print("Seed data already exists — skipping.")
            return

        org = Organization(
            name="Beacon Church",
            slug="beacon",
            description="First field office — Beacon Church",
        )
        db.add(org)
        await db.flush()

        users = [
            User(
                email="admin@beacon.church",
                hashed_password=hash_password("Admin123!"),
                display_name="Beacon Admin",
                role=UserRole.ADMIN,
                organization_id=org.id,
            ),
            User(
                email="leader@beacon.church",
                hashed_password=hash_password("Leader123!"),
                display_name="Agent Handler",
                role=UserRole.LEADER,
                organization_id=org.id,
            ),
            User(
                email="parent@beacon.church",
                hashed_password=hash_password("Parent123!"),
                display_name="Parent Smith",
                role=UserRole.PARENT,
                organization_id=org.id,
                kid_mode_pin="1234",
            ),
        ]
        db.add_all(users)
        await db.commit()
        print(f"Seeded org '{org.name}' with {len(users)} users.")


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
