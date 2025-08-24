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
from apps.alchohalt.auth import issue_magic_link


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_magic_link_flow(capsys):
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/request_link", json={"email": "a@b.com", "tz": "UTC"})
            assert r.status_code == 200
            out = capsys.readouterr().out
            token = out.strip().split("token=")[-1].strip()
            r = await ac.get(f"/alchohalt/magic?token={token}", follow_redirects=False)
            assert r.status_code == 303
            assert "alc_session" in r.cookies
            r = await ac.get("/alchohalt/ui")
            assert "Dashboard" in r.text
            bad = await ac.get("/alchohalt/magic?token=bad", follow_redirects=False)
            assert bad.status_code == 400
            expired = issue_magic_link("x@y.com", expires_in=-1)
            exp = await ac.get(f"/alchohalt/magic?token={expired}", follow_redirects=False)
            assert exp.status_code == 400
    asyncio.run(inner())


def test_sms_log_when_no_creds(capsys):
    from apps.alchohalt.service import send_sms

    send_sms("+15550001", "hi")
    assert "sms to" in capsys.readouterr().out
