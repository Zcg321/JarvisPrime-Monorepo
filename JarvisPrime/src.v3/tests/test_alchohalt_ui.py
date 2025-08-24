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
from sqlmodel import SQLModel, Session
from apps.alchohalt.models import User
from apps.alchohalt.auth import sign_session


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_ui_flow():
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.get("/alchohalt/ui")
            assert r.status_code == 200
            assert "Send Link" in r.text
            with Session(engine) as s:
                u = User(email="a@b.com", tz="UTC")
                s.add(u)
                s.commit()
                s.refresh(u)
                cookie = sign_session(u.id)
            ac.cookies.set("alc_session", cookie)
            r = await ac.get("/alchohalt/ui")
            assert "Dashboard" in r.text
            r = await ac.post("/alchohalt/ui/checkin", data={"status": "halted"})
            assert r.status_code == 303
            r = await ac.get("/alchohalt/ui")
            assert "halted" in r.text
            r = await ac.post("/alchohalt/ui/consent", data={"consent": "true"})
            assert r.status_code == 303
            r = await ac.post(
                "/alchohalt/ui/caregivers/add",
                data={"caregiver_email": "c@e.com", "role": "viewer"},
            )
            assert r.status_code == 303
            r = await ac.post(
                "/alchohalt/invite_caregiver",
                data={"user_id": u.id, "caregiver_email": "d@e.com", "role": "viewer"},
            )
            assert r.status_code == 200
            r = await ac.get("/alchohalt/ui")
            assert "c@e.com" in r.text
    asyncio.run(inner())
