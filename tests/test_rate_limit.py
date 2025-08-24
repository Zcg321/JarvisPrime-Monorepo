import os
import sys
from pathlib import Path
from datetime import timedelta
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
from apps.alchohalt.app import app, engine, _utcnow  # noqa: E402
from sqlmodel import SQLModel


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_rate_limit(monkeypatch):
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/users", json={"email": "u@e.com", "tz": "UTC"})
            uid = r.json()["id"]
            for _ in range(5):
                res = await ac.post("/alchohalt/checkins", json={"user_id": uid, "status": "halted"})
                assert res.status_code == 200
            res = await ac.post("/alchohalt/checkins", json={"user_id": uid, "status": "slipped"})
            assert res.status_code == 429
            tomorrow = _utcnow() + timedelta(days=1)
            monkeypatch.setattr("apps.alchohalt.app._utcnow", lambda: tomorrow)
            res = await ac.post("/alchohalt/checkins", json={"user_id": uid, "status": "halted"})
            assert res.status_code == 200
    asyncio.run(inner())
