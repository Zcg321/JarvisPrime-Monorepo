import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from pathlib import Path
import os, sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
from apps.alchohalt.app import app, engine  # noqa: E402


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_bulk_checkins_flow():
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/users", json={"email": "a@b.com", "tz": "UTC"})
            uid = r.json()["id"]
            r = await ac.post(
                "/alchohalt/checkins/bulk",
                json={
                    "user_id": uid,
                    "items": [
                        {"status": "halted"},
                        {"status": "slipped", "date": "2024-01-02"},
                    ],
                },
            )
            assert r.json()["processed"] == 2
            today = datetime.utcnow().date().isoformat()
            r = await ac.get(f"/alchohalt/export/{uid}")
            data = r.json()["checkins"]
            assert any(c["date"] == today for c in data)
            await ac.post(
                "/alchohalt/checkins/bulk",
                json={"user_id": uid, "items": [{"status": "slipped"}]},
            )
            r = await ac.get(f"/alchohalt/export/{uid}")
            data = r.json()["checkins"]
            assert any(c["status"] == "slipped" and c["date"] == today for c in data)
            r = await ac.post(
                "/alchohalt/checkins/bulk",
                json={"user_id": uid, "items": [{"status": "oops"}]},
            )
            assert r.status_code == 400
    asyncio.run(inner())
