"""
Integration tests for bot lifecycle transitions (start/pause/stop) against
a real Postgres instance. These are marked `integration` and require the
docker-compose stack running — unlike the pure-logic tests elsewhere in
this suite, mocking SQLAlchemy session/commit behavior would be more
fragile than the code it's testing. Run via `make test`.
"""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.models import BotStatus, User

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session):
    user = User(email=f"test-{uuid.uuid4()}@example.com", hashed_password=hash_password("testpass123"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    yield user
    await db_session.delete(user)
    await db_session.commit()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.mark.integration
async def test_bot_lifecycle_start_pause_stop(client, test_user):
    """A bot must move STOPPED -> RUNNING -> PAUSED -> RUNNING -> STOPPED
    and reject invalid transitions (e.g. pausing an already-stopped bot)."""
    token = await _login(client, test_user.email, "testpass123")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post(
        "/api/v1/bots",
        json={
            "name": "test-bot",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "strategy_name": "rsi",
            "strategy_params": {"period": 14},
            "mode": "paper",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    bot_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == BotStatus.STOPPED

    # Pausing a stopped bot should be rejected
    pause_resp = await client.post(f"/api/v1/bots/{bot_id}/pause", headers=headers)
    assert pause_resp.status_code == 400

    start_resp = await client.post(f"/api/v1/bots/{bot_id}/start", headers=headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == BotStatus.RUNNING
    assert start_resp.json()["is_active"] is True

    pause_resp = await client.post(f"/api/v1/bots/{bot_id}/pause", headers=headers)
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] == BotStatus.PAUSED
    assert pause_resp.json()["is_active"] is False

    resume_resp = await client.post(f"/api/v1/bots/{bot_id}/start", headers=headers)
    assert resume_resp.status_code == 200
    assert resume_resp.json()["status"] == BotStatus.RUNNING

    stop_resp = await client.post(f"/api/v1/bots/{bot_id}/stop", headers=headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == BotStatus.STOPPED

    await client.delete(f"/api/v1/bots/{bot_id}", headers=headers)


@pytest.mark.integration
async def test_cannot_access_another_users_bot(client, test_user, db_session):
    """Ownership checks must 404 (not 403) so bot existence isn't leaked
    to users who don't own it."""
    other_user = User(email=f"other-{uuid.uuid4()}@example.com", hashed_password=hash_password("otherpass123"))
    db_session.add(other_user)
    await db_session.commit()

    token_a = await _login(client, test_user.email, "testpass123")
    token_b = await _login(client, other_user.email, "otherpass123")

    create_resp = await client.post(
        "/api/v1/bots",
        json={"name": "owned-by-a", "symbol": "ETH/USDT", "strategy_name": "macd", "strategy_params": {}},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    bot_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/bots/{bot_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert get_resp.status_code == 404

    await client.delete(f"/api/v1/bots/{bot_id}", headers={"Authorization": f"Bearer {token_a}"})
    await db_session.delete(other_user)
    await db_session.commit()
