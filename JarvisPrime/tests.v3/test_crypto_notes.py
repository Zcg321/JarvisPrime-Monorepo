import os
import sys
from pathlib import Path
import asyncio
from cryptography.fernet import Fernet
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import Session, SQLModel, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"

from apps.alchohalt.app import app, engine  # noqa: E402
from apps.alchohalt.models import Checkin  # noqa: E402
from apps.alchohalt.crypto import get_fernet  # noqa: E402


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_encrypted_notes_roundtrip():
    key = Fernet.generate_key().decode()
    os.environ["ALC_CRYPTO_KEY"] = key
    get_fernet.cache_clear()

    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/users", json={"email": "a@b.com", "tz": "UTC"})
            uid = r.json()["id"]
            await ac.post("/alchohalt/checkins", json={"user_id": uid, "status": "halted", "note": "secret"})
            with Session(engine) as session:
                chk = session.exec(select(Checkin).where(Checkin.user_id == uid)).one()
                assert chk.note != "secret"
            r = await ac.get(f"/alchohalt/export/{uid}")
            assert r.json()["checkins"][0]["note"] == "secret"
            r = await ac.get(f"/alchohalt/export_csv/{uid}")
            assert "note" not in r.text.splitlines()[0]
            r = await ac.get(f"/alchohalt/export_csv/{uid}?include_notes=1")
            assert "secret" in r.text
    asyncio.run(inner())


def test_plain_when_no_key():
    os.environ.pop("ALC_CRYPTO_KEY", None)
    get_fernet.cache_clear()

    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post("/alchohalt/users", json={"email": "b@b.com", "tz": "UTC"})
            uid = r.json()["id"]
            await ac.post("/alchohalt/checkins", json={"user_id": uid, "status": "halted", "note": "hi"})
            with Session(engine) as session:
                chk = session.exec(select(Checkin).where(Checkin.user_id == uid)).one()
                assert chk.note == "hi"
    asyncio.run(inner())
