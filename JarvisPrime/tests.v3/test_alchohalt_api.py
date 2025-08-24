import os
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
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

def test_api_flow():
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/users", json={"email": "a@b.com", "tz": "UTC"})
            user_id = r.json()["id"]
            await ac.post("/alchohalt/checkins", json={"user_id": user_id, "status": "halted"})
            r = await ac.get(f"/alchohalt/export/{user_id}")
            data = r.json()
            today = datetime.utcnow().date().isoformat()
            assert data["checkins"][0]["date"] == today
            assert data["checkins"][0]["status"] == "halted"
            await ac.post("/alchohalt/checkins", json={"user_id": user_id, "status": "slipped"})
            r = await ac.get(f"/alchohalt/export/{user_id}")
            assert r.json()["checkins"][0]["status"] == "slipped"
    asyncio.run(inner())


def test_timezone_default_today_and_csv_metrics():
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            tzs = ["UTC", "Asia/Tokyo"]
            ids = []
            for tz in tzs:
                r = await ac.post("/alchohalt/users", json={"email": f"{tz}@x.com", "tz": tz})
                uid = r.json()["id"]
                ids.append((uid, tz))
                await ac.post("/alchohalt/checkins", json={"user_id": uid, "status": "halted"})
                r = await ac.get(f"/alchohalt/export/{uid}")
                exp = datetime.now(ZoneInfo(tz)).date().isoformat()
                assert r.json()["checkins"][0]["date"] == exp
            user_id = ids[0][0]
            await ac.post(
                "/alchohalt/checkins",
                json={"user_id": user_id, "status": "slipped", "date": "2024-01-02", "note": "oops"},
            )
            r = await ac.get(f"/alchohalt/export_csv/{user_id}")
            csv_data = r.text
            assert "note" not in csv_data.splitlines()[0]
            files = {"file": ("data.csv", csv_data, "text/csv")}
            r = await ac.post(
                "/alchohalt/import_csv",
                data={"email": "b@b.com", "tz": "UTC"},
                files=files,
            )
            new_id = r.json()["id"]
            r = await ac.get(f"/alchohalt/export/{new_id}")
            assert len(r.json()["checkins"]) == 2
            r = await ac.get("/alchohalt/metrics")
            m = r.json()
            assert "users" in m and m["users"] >= 2
            assert "checkins_total" in m
            assert "encrypted_notes" in m
    asyncio.run(inner())
