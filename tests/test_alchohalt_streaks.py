import os
import sys
from pathlib import Path
from datetime import date, timedelta
from sqlmodel import SQLModel, Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
os.environ["ALC_DB_URL"] = "sqlite://"
from apps.alchohalt.app import engine  # noqa: E402
from apps.alchohalt.models import User, Checkin
from apps.alchohalt.service import calculate_streaks


def setup_module():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_streak_edges():
    with Session(engine) as session:
        user = User(email="a@b.com", tz="UTC")
        session.add(user)
        session.commit()
        session.refresh(user)
        base = date(2024, 1, 1)
        session.add(Checkin(user_id=user.id, date=base, status="halted"))
        session.commit()
        res = calculate_streaks(session, user, base)
        assert res["current_streak_days"] == 1
        assert res["longest_streak_days"] == 1
        session.add(Checkin(user_id=user.id, date=base + timedelta(days=1), status="slipped"))
        session.commit()
        res = calculate_streaks(session, user, base + timedelta(days=1))
        assert res["current_streak_days"] == 0
        session.add(Checkin(user_id=user.id, date=base + timedelta(days=3), status="halted"))
        session.commit()
        res = calculate_streaks(session, user, base + timedelta(days=3))
        assert res["current_streak_days"] == 1
        user2 = User(email="b@b.com", tz="UTC")
        session.add(user2)
        session.commit()
        session.refresh(user2)
        start = date(2024, 2, 1)
        for i in range(7):
            session.add(Checkin(user_id=user2.id, date=start + timedelta(days=i), status="halted"))
        session.commit()
        res = calculate_streaks(session, user2, start + timedelta(days=6))
        assert res["last_30"]["halted"] == 7

        user3 = User(email="c@b.com", tz="UTC")
        session.add(user3)
        session.commit()
        session.refresh(user3)
        base3 = date(2024, 3, 1)
        session.add(Checkin(user_id=user3.id, date=base3, status="halted"))
        session.add(Checkin(user_id=user3.id, date=base3 + timedelta(days=2), status="halted"))
        session.commit()
        res = calculate_streaks(session, user3, base3 + timedelta(days=2))
        assert res["longest_streak_days"] == 1
