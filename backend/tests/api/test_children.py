"""Tests for child profiles, Kid Mode, consent, data export/delete."""

import pytest
from httpx import AsyncClient

from app.models.organization import Organization
from app.models.user import User
from tests.conftest import get_auth_headers


@pytest.mark.asyncio
class TestChildProfiles:
    async def test_create_child_requires_pin(self, client: AsyncClient, parent_user: User):
        headers = await get_auth_headers(client, "parent@test.com", "TestPass123!")
        resp = await client.post(
            "/api/v1/children/",
            json={"codename": "Shadow Fox", "age_band": "7-8"},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "PIN" in resp.json()["detail"]

    async def test_set_pin_then_create_child(self, client: AsyncClient, parent_user: User):
        headers = await get_auth_headers(client, "parent@test.com", "TestPass123!")

        pin_resp = await client.post(
            "/api/v1/children/pin", json={"pin": "5678"}, headers=headers
        )
        assert pin_resp.status_code == 204

        resp = await client.post(
            "/api/v1/children/",
            json={"codename": "Shadow Fox", "age_band": "7-8", "avatar": "lion"},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codename"] == "Shadow Fox"
        assert data["age_band"] == "7-8"
        assert data["avatar"] == "lion"

    async def test_create_child_with_pin_parent(
        self, client: AsyncClient, parent_with_pin: User
    ):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        resp = await client.post(
            "/api/v1/children/",
            json={"codename": "Eagle Eye", "age_band": "9-11"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["codename"] == "Eagle Eye"

    async def test_list_children(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        await client.post(
            "/api/v1/children/",
            json={"codename": "Agent Alpha", "age_band": "7-8"},
            headers=headers,
        )
        await client.post(
            "/api/v1/children/",
            json={"codename": "Agent Bravo", "age_band": "9-11"},
            headers=headers,
        )
        resp = await client.get("/api/v1/children/", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_get_child(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Storm Rider", "age_band": "7-8"},
            headers=headers,
        )
        child_id = create.json()["id"]
        resp = await client.get(f"/api/v1/children/{child_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["codename"] == "Storm Rider"

    async def test_update_child(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Old Name", "age_band": "7-8"},
            headers=headers,
        )
        child_id = create.json()["id"]
        resp = await client.patch(
            f"/api/v1/children/{child_id}",
            json={"codename": "New Codename", "avatar": "eagle"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["codename"] == "New Codename"
        assert resp.json()["avatar"] == "eagle"

    async def test_other_parent_cannot_see_child(
        self,
        client: AsyncClient,
        parent_with_pin: User,
        org_beacon: Organization,
    ):
        headers_a = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Secret Agent", "age_band": "9-11"},
            headers=headers_a,
        )
        child_id = create.json()["id"]

        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "other-parent@test.com",
                "password": "TestPass123!",
                "display_name": "Other Parent",
                "organization_slug": "beacon",
            },
        )
        token_b = register.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp = await client.get(f"/api/v1/children/{child_id}", headers=headers_b)
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestRankProgression:
    async def test_new_child_is_trainee(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        resp = await client.post(
            "/api/v1/children/",
            json={"codename": "Rank Rookie", "age_band": "9-11"},
            headers=headers,
        )
        data = resp.json()
        assert data["xp"] == 0
        assert data["rank_info"]["rank"] == "trainee"
        assert data["rank_info"]["designation"] == "Agent 0"

    async def test_award_xp(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "XP Agent", "age_band": "9-11"},
            headers=headers,
        )
        child_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/children/{child_id}/xp",
            json={"amount": 100},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["xp_awarded"] == 100
        assert data["child"]["xp"] == 100
        assert data["ranked_up"] is False

    async def test_rank_up_to_scout(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Rank Up Agent", "age_band": "9-11"},
            headers=headers,
        )
        child_id = create.json()["id"]

        resp = await client.post(
            f"/api/v1/children/{child_id}/xp",
            json={"amount": 250},
            headers=headers,
        )
        data = resp.json()
        assert data["ranked_up"] is True
        assert data["old_rank"] == "trainee"
        assert data["new_rank"] == "scout"
        assert data["child"]["rank_info"]["designation"] == "Agent 1"

    async def test_rank_progression_full(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Max Agent", "age_band": "9-11"},
            headers=headers,
        )
        child_id = create.json()["id"]

        # Jump straight to Commander
        resp = await client.post(
            f"/api/v1/children/{child_id}/xp",
            json={"amount": 500},
            headers=headers,
        )
        # Multiple smaller awards to reach top
        for _ in range(12):
            resp = await client.post(
                f"/api/v1/children/{child_id}/xp",
                json={"amount": 500},
                headers=headers,
            )

        data = resp.json()
        assert data["child"]["rank_info"]["rank"] == "commander"
        assert data["child"]["rank_info"]["designation"] == "Agent 001"
        assert data["child"]["rank_info"]["xp_to_next_rank"] is None


@pytest.mark.asyncio
class TestKidMode:
    async def test_enter_kid_mode(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Kid Agent", "age_band": "7-8"},
            headers=headers,
        )
        child_id = create.json()["id"]

        resp = await client.post(
            "/api/v1/children/kid-mode/enter",
            json={"child_id": child_id},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["child"]["codename"] == "Kid Agent"
        assert "token" in data

    async def test_exit_kid_mode_correct_pin(
        self, client: AsyncClient, parent_with_pin: User
    ):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        resp = await client.post(
            "/api/v1/children/kid-mode/exit",
            json={"pin": "1234"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "exited"

    async def test_exit_kid_mode_wrong_pin(
        self, client: AsyncClient, parent_with_pin: User
    ):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        resp = await client.post(
            "/api/v1/children/kid-mode/exit",
            json={"pin": "0000"},
            headers=headers,
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
class TestPrivacyAndConsent:
    async def test_privacy_notice_available(self, client: AsyncClient):
        resp = await client.get("/api/v1/children/privacy-notice")
        assert resp.status_code == 200
        data = resp.json()
        assert "version" in data
        assert "COPPA" in data["text"]
        assert "What we collect" in data["text"]

    async def test_export_child_data(self, client: AsyncClient, parent_with_pin: User):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Export Kid", "age_band": "7-8"},
            headers=headers,
        )
        child_id = create.json()["id"]

        resp = await client.get(f"/api/v1/children/{child_id}/export", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["child"]["codename"] == "Export Kid"
        assert len(data["consents"]) >= 1

    async def test_delete_child_requires_pin(
        self, client: AsyncClient, parent_with_pin: User
    ):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Doomed Agent", "age_band": "9-11"},
            headers=headers,
        )
        child_id = create.json()["id"]

        resp = await client.request(
            "DELETE",
            f"/api/v1/children/{child_id}",
            headers=headers,
            json={"pin": "0000"},
        )
        assert resp.status_code == 403

    async def test_delete_child_with_correct_pin(
        self, client: AsyncClient, parent_with_pin: User
    ):
        headers = await get_auth_headers(client, "pinparent@test.com", "TestPass123!")
        create = await client.post(
            "/api/v1/children/",
            json={"codename": "Deleted Agent", "age_band": "9-11"},
            headers=headers,
        )
        child_id = create.json()["id"]

        resp = await client.request(
            "DELETE",
            f"/api/v1/children/{child_id}",
            headers=headers,
            json={"pin": "1234"},
        )
        assert resp.status_code == 204

        get_resp = await client.get(f"/api/v1/children/{child_id}", headers=headers)
        assert get_resp.status_code == 404
