import pytest
from httpx import AsyncClient

from app.models.organization import Organization
from app.models.user import User


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient, org_beacon: Organization):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new@example.com",
                "password": "SecurePass1!",
                "display_name": "New Agent",
                "organization_slug": "beacon",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient, parent_user: User):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "parent@test.com",
                "password": "SecurePass1!",
                "display_name": "Duplicate",
                "organization_slug": "beacon",
            },
        )
        assert resp.status_code == 409

    async def test_register_bad_org(self, client: AsyncClient, org_beacon: Organization):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nobody@example.com",
                "password": "SecurePass1!",
                "display_name": "Lost",
                "organization_slug": "nonexistent",
            },
        )
        assert resp.status_code == 404

    async def test_register_short_password(self, client: AsyncClient, org_beacon: Organization):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
                "display_name": "Short Pass",
                "organization_slug": "beacon",
            },
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient, parent_user: User):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "parent@test.com", "password": "TestPass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, parent_user: User):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "parent@test.com", "password": "WrongPassword1!"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@test.com", "password": "Whatever1!"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestTokenRefresh:
    async def test_refresh_success(self, client: AsyncClient, parent_user: User):
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "parent@test.com", "password": "TestPass123!"},
        )
        refresh_token = login.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "garbage"}
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestMe:
    async def test_me_authenticated(self, client: AsyncClient, parent_user: User):
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "parent@test.com", "password": "TestPass123!"},
        )
        token = login.json()["access_token"]

        resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "parent@test.com"
        assert data["role"] == "parent"

    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403
