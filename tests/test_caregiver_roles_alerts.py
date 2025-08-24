import os, sys
from pathlib import Path
import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
from apps.alchohalt.app import app, engine  # noqa: E402
from sqlmodel import SQLModel, Session, select
from apps.alchohalt.models import User, Checkin, CaregiverLink, AlertPref  # noqa: E402
from apps.alchohalt.service import evaluate_alerts_for, notify_caregivers  # noqa: E402


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_caregiver_flow_and_alerts(monkeypatch, tmp_path):
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with Session(engine) as s:
                u = User(email="u@e.com", tz="UTC", consent_caregiver=False, phone="123")
                s.add(u)
                s.commit()
                s.refresh(u)
                user_id = u.id
            r = await ac.post("/alchohalt/caregivers", json={"user_id": user_id, "caregiver_email": "c@e.com", "role": "supporter"})
            assert r.status_code == 403
            await ac.post("/alchohalt/consent", json={"user_id": user_id, "consent": True})
            r = await ac.post("/alchohalt/caregivers", json={"user_id": user_id, "caregiver_email": "c@e.com", "role": "supporter"})
            assert r.status_code == 200
            r = await ac.get(f"/alchohalt/caregivers/{user_id}")
            assert "c***@e.com" in r.text
            await ac.post(
                "/alchohalt/alert_prefs",
                json={"user_id": user_id, "channel": "email", "threshold": "slip"},
            )
            r = await ac.get(f"/alchohalt/alert_prefs/{user_id}")
            assert r.json()[0]["threshold"] == "slip"
            with Session(engine) as s:
                today = datetime.now(ZoneInfo("UTC")).date()
                s.add(Checkin(user_id=user_id, date=today, status="slipped"))
                s.commit()
                u = s.get(User, user_id)
                log = tmp_path / "alchohalt.jsonl"
                monkeypatch.setattr("apps.alchohalt.service.LOG_FILE", log)
                events = evaluate_alerts_for(s, u, datetime.now(ZoneInfo("UTC")))
                sent = {}
                def fake_email(*a, **k):
                    sent["email"] = sent.get("email", 0) + 1
                monkeypatch.setattr("apps.alchohalt.service.send_email", fake_email)
                res = notify_caregivers(s, u, events, dry_run=False)
                assert sent.get("email") == 1
                assert res["alerts_sent"] == 1
                data = log.read_text().strip().splitlines()
                assert data and "alert" in data[-1]
                # quiet hours block
                pref = s.exec(select(AlertPref).where(AlertPref.user_id == user_id).limit(1)).first()
                pref.quiet_hours_start = 0
                pref.quiet_hours_end = 23
                s.commit()
                events2 = evaluate_alerts_for(s, u, datetime.now(ZoneInfo("UTC")))
                assert events2 == []
        return True
    asyncio.run(inner())
