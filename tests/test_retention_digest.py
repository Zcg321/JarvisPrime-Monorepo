import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
from zoneinfo import ZoneInfo
import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel, Session, select

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
os.environ["ALC_RETENTION_DAYS"] = "1"

from apps.alchohalt.app import app, engine  # noqa: E402
from apps.alchohalt.models import User, Checkin  # noqa: E402
from apps.alchohalt.service import redact_old_notes, send_digest_if_due  # noqa: E402


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_retention_and_digest(capsys):
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            r = await ac.post(
                "/alchohalt/users",
                json={"email": "x@a.com", "tz": "UTC"},
            )
            uid = r.json()["id"]
        with Session(engine) as session:
            user = session.get(User, uid)
            user.caregiver_email = "c@d.com"
            session.commit()
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            old_date = (datetime.now() - timedelta(days=2)).date()
            await ac.post(
                "/alchohalt/checkins",
                json={"user_id": uid, "status": "halted", "date": old_date.isoformat(), "note": "old"},
            )
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            await ac.post(
                "/alchohalt/checkins",
                json={"user_id": uid, "status": "slipped", "date": yesterday},
            )
            with Session(engine) as session:
                cutoff = datetime.now().date() - timedelta(days=1)
                redact_old_notes(session, cutoff)
                chk = session.exec(
                    select(Checkin).where(Checkin.user_id == uid, Checkin.date == old_date)
                ).first()
                assert chk.note is None
                sent = send_digest_if_due(
                    session,
                    session.get(User, uid),
                    datetime.now(ZoneInfo("UTC")).replace(hour=0, minute=0, second=0, microsecond=0),
                    dry_run=True,
                )
                assert sent
    asyncio.run(inner())
