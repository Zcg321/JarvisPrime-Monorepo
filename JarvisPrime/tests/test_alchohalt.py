from datetime import date
from alchohalt import metrics, schedule
import subprocess, sys, os, json
from alchohalt.store import AHState, AHEntry


def sample_state() -> AHState:
    entries = {
        "2023-09-30": AHEntry("2023-09-30", "halted"),
        "2023-10-01": AHEntry("2023-10-01", "halted"),
        "2023-10-02": AHEntry("2023-10-02", "slipped"),
        "2023-10-03": AHEntry("2023-10-03", "halted"),
    }
    return AHState(entries=entries)


def test_streak_and_last_slip():
    state = sample_state()
    stats = metrics(state=state, today=date(2023, 10, 3))
    assert stats["streak"] == 1
    assert stats["lastSlipDate"] == "2023-10-02"


def test_aggregates():
    state = sample_state()
    stats = metrics(state=state, today=date(2023, 10, 3))
    assert stats["halted7"] == 3
    assert stats["halted30"] == 3
    assert stats["series7"][-1] == 1  # today


def test_schedule_stub(caplog):
    caplog.set_level("INFO")
    schedule(21, 0)
    assert any("schedule reminder" in r.message for r in caplog.records)


def test_cli_stats():
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    proc = subprocess.run(
        [sys.executable, "-m", "alchohalt.cli", "stats"],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert "streak" in data
