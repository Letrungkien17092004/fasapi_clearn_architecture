"""Integration tests — verify the full HTTP → Use Case → DB pipeline.

These tests use an in-memory SQLite database and mock the auth service,
demonstrating how to test the Composition Root wiring end-to-end.

Run with:
    pytest tests/test_api_integration.py -v
"""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import UUID

import httpx
import pytest
import pytest_asyncio

from app.domain.entities import User
from app.infrastructure.database import dispose_db, init_db


# ── Constants ──────────────────────────────────────────────────────

MOCK_USER = User(
    id=UUID("11111111-1111-1111-1111-111111111111"),
    email="test@example.com",
    name="Test User",
)

AUTH_HEADERS = {"Authorization": "Bearer fake-jwt-token-for-testing"}


# ── Fixtures ───────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client():
    """Yield an async HTTP client wired to a fully-booted test app.

    1. Initialise the in-memory database.
    2. Mock the auth service to always return MOCK_USER.
    3. Yield an httpx.AsyncClient for making requests.
    4. Dispose the database on teardown.
    """
    # Import the app factory fresh to avoid state leakage.
    from main import create_app

    app = create_app()

    # Boot the in-memory database (tables created via init_db).
    await init_db("sqlite+aiosqlite://")

    # Mock the auth service.
    mock_auth = AsyncMock()
    mock_auth.verify_token = AsyncMock(return_value=MOCK_USER)
    app.state.auth_service = mock_auth

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac

    await dispose_db()


# ── Tests ──────────────────────────────────────────────────────────


class TestHealthEndpoint:
    """Verify the unprotected health check."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client: httpx.AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestTaskCRUD:
    """Full lifecycle: create → read → update → delete."""

    @pytest.mark.asyncio
    async def test_create_task(self, client: httpx.AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/tasks",
            json={"title": "Learn DDD", "description": "Study domain-driven design"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Learn DDD"
        assert data["status"] == "pending"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_tasks(self, client: httpx.AsyncClient) -> None:
        # Seed a task.
        await client.post(
            "/api/v1/tasks",
            json={"title": "Seed"},
            headers=AUTH_HEADERS,
        )

        resp = await client.get("/api/v1/tasks", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert isinstance(data["tasks"], list)

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, client: httpx.AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/tasks",
            json={"title": "Fetch me"},
            headers=AUTH_HEADERS,
        )
        task_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/tasks/{task_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["id"] == task_id

    @pytest.mark.asyncio
    async def test_update_task_status(self, client: httpx.AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/tasks",
            json={"title": "Update me"},
            headers=AUTH_HEADERS,
        )
        task_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"status": "completed"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_task(self, client: httpx.AsyncClient) -> None:
        create_resp = await client.post(
            "/api/v1/tasks",
            json={"title": "Delete me"},
            headers=AUTH_HEADERS,
        )
        task_id = create_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/tasks/{task_id}", headers=AUTH_HEADERS
        )
        assert del_resp.status_code == 204

        # Confirm it's gone.
        get_resp = await client.get(
            f"/api/v1/tasks/{task_id}", headers=AUTH_HEADERS
        )
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_returns_404(
        self, client: httpx.AsyncClient
    ) -> None:
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = await client.get(f"/api/v1/tasks/{fake_id}", headers=AUTH_HEADERS)
        assert resp.status_code == 404


class TestAuthentication:
    """Verify that unauthenticated requests are rejected."""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(
        self, client: httpx.AsyncClient
    ) -> None:
        resp = await client.get("/api/v1/tasks")
        assert resp.status_code == 401
