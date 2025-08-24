from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from alchohalt.store import AHState, checkin, metrics
from alchohalt.notify import schedule_daily


def test_streak_across_month():
    state = AHState()
    checkin(state, "halted", day=date(2024, 2, 27))
    checkin(state, "halted", day=date(2024, 2, 28))
    checkin(state, "slipped", day=date(2024, 3, 1))
    checkin(state, "halted", day=date(2024, 3, 2))

    m = metrics(state, today=date(2024, 3, 2))
    assert m["streak"] == 1
    assert m["last_slip_date"] == "2024-03-01"


def test_aggregates_and_series():
    state = AHState()
    today = date(2024, 3, 30)
    for i in range(30):
        d = today - timedelta(days=i)
        status = "halted" if i % 2 == 0 else "slipped"
        checkin(state, status, day=d)

    m = metrics(state, today=today)
    assert m["halted7"] == 4
    assert m["halted30"] == 15
    assert m["series7"] == [1 if i % 2 == 0 else 0 for i in range(6, -1, -1)]


def test_schedule_stub(capsys):
    msg = schedule_daily(21, 0)
    captured = capsys.readouterr().out
    assert "21:00" in captured
    assert msg == "Reminder scheduled daily at 21:00"
