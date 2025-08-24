import os
import sys
from pathlib import Path
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
from apps.alchohalt.app import app, engine  # noqa: E402
from sqlmodel import SQLModel


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_caregiver_view():
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/users", json={"email": "a@b.com", "tz": "UTC"})
            user_id = r.json()["id"]
            await ac.post("/alchohalt/checkins", json={"user_id": user_id, "status": "halted"})
            r = await ac.get(f"/alchohalt/export/{user_id}")
            public_id = r.json()["user"]["public_id"]
            r = await ac.get(f"/alchohalt/care/{public_id}")
            assert r.status_code == 200
            assert "halted" in r.text
            assert "Check in" not in r.text
            assert "@" not in r.text
    asyncio.run(inner())
