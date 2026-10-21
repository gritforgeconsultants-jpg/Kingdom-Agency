import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.organization import Organization
from app.models.user import User, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def org_beacon(db: AsyncSession) -> Organization:
    org = Organization(name="Beacon Church", slug="beacon", description="Test church")
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


@pytest.fixture
async def org_other(db: AsyncSession) -> Organization:
    org = Organization(name="Other Church", slug="other-church", description="Another church")
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


async def create_test_user(
    db: AsyncSession,
    org: Organization,
    role: UserRole = UserRole.PARENT,
    email: str | None = None,
) -> User:
    user = User(
        email=email or f"{role.value}-{uuid.uuid4().hex[:8]}@test.com",
        hashed_password=hash_password("TestPass123!"),
        display_name=f"Test {role.value.title()}",
        role=role,
        organization_id=org.id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_auth_headers(client: AsyncClient, email: str, password: str) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def parent_user(db: AsyncSession, org_beacon: Organization) -> User:
    return await create_test_user(db, org_beacon, UserRole.PARENT, "parent@test.com")


@pytest.fixture
async def admin_user(db: AsyncSession, org_beacon: Organization) -> User:
    return await create_test_user(db, org_beacon, UserRole.ADMIN, "admin@test.com")


@pytest.fixture
async def leader_user(db: AsyncSession, org_beacon: Organization) -> User:
    return await create_test_user(db, org_beacon, UserRole.LEADER, "leader@test.com")


@pytest.fixture
async def other_org_admin(db: AsyncSession, org_other: Organization) -> User:
    return await create_test_user(db, org_other, UserRole.ADMIN, "other-admin@test.com")
