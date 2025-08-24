import os
import sys
import asyncio
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
from apps.alchohalt.app import app, engine  # noqa: E402
from sqlmodel import SQLModel, Session, select
from apps.alchohalt.models import User, CaregiverLink  # noqa: E402
from apps.alchohalt.auth import sign_session, issue_caregiver_invite  # noqa: E402


@pytest.fixture(autouse=True)
def clear_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield


def test_rbac_and_invite_flow():
    async def inner():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # create two users
            with Session(engine) as s:
                u1 = User(email="a@b.com", tz="UTC", consent_caregiver=True)
                u2 = User(email="c@d.com", tz="UTC")
                s.add(u1)
                s.add(u2)
                s.commit()
                s.refresh(u1); s.refresh(u2)
                cookie1 = sign_session(u1.id)
            # mismatched owner
            ac.cookies.set("alc_session", cookie1)
            r = await ac.post("/alchohalt/checkins", json={"user_id": u2.id, "status": "halted"})
            assert r.status_code == 403
            # invite & accept
            r = await ac.post(
                "/alchohalt/invite_caregiver",
                data={"user_id": u1.id, "caregiver_email": "care@ex.com", "role": "viewer"},
            )
            assert r.status_code == 200
            token = issue_caregiver_invite(u1.id, "care@ex.com", "viewer", expires_in=60)
            r = await ac.get(f"/alchohalt/accept_caregiver?token={token}")
            assert r.status_code == 303
            with Session(engine) as s:
                links = s.exec(select(CaregiverLink).where(CaregiverLink.user_id == u1.id)).all()
                assert len(links) == 1
            # expired token
            bad = issue_caregiver_invite(u1.id, "care@ex.com", "viewer", expires_in=-1)
            r = await ac.get(f"/alchohalt/accept_caregiver?token={bad}")
            assert r.status_code == 400
    asyncio.run(inner())
