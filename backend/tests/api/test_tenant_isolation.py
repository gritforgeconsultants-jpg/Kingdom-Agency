"""Tenant isolation tests: users in org A cannot see/modify org B data."""

import pytest
from httpx import AsyncClient

from app.models.organization import Organization
from app.models.user import User
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
class TestTenantIsolation:
    async def test_admin_only_sees_own_org_users(
        self,
        client: AsyncClient,
        admin_user: User,
        other_org_admin: User,
        org_beacon: Organization,
        org_other: Organization,
    ):
        headers = await get_auth_headers(client, "admin@test.com", "TestPass123!")
        resp = await client.get("/api/v1/organizations/mine/users", headers=headers)
        assert resp.status_code == 200
        users = resp.json()
        org_ids = {u["organization_id"] for u in users}
        assert org_ids == {str(org_beacon.id)}

    async def test_other_admin_sees_only_their_org(
        self,
        client: AsyncClient,
        admin_user: User,
        other_org_admin: User,
        org_other: Organization,
    ):
        headers = await get_auth_headers(client, "other-admin@test.com", "TestPass123!")
        resp = await client.get("/api/v1/organizations/mine/users", headers=headers)
        assert resp.status_code == 200
        users = resp.json()
        org_ids = {u["organization_id"] for u in users}
        assert org_ids == {str(org_other.id)}

    async def test_admin_cannot_modify_other_org_user(
        self,
        client: AsyncClient,
        admin_user: User,
        other_org_admin: User,
    ):
        headers = await get_auth_headers(client, "admin@test.com", "TestPass123!")
        resp = await client.put(
            f"/api/v1/organizations/mine/users/{other_org_admin.id}/role?role=leader",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_parent_cannot_list_org_users(
        self,
        client: AsyncClient,
        parent_user: User,
    ):
        headers = await get_auth_headers(client, "parent@test.com", "TestPass123!")
        resp = await client.get("/api/v1/organizations/mine/users", headers=headers)
        assert resp.status_code == 403

    async def test_my_org_returns_only_own_org(
        self,
        client: AsyncClient,
        admin_user: User,
        org_beacon: Organization,
    ):
        headers = await get_auth_headers(client, "admin@test.com", "TestPass123!")
        resp = await client.get("/api/v1/organizations/mine", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["slug"] == "beacon"
