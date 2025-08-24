import json
from pathlib import Path
import types

from scripts import cron_clock_drift
from src.serve import alerts


def test_clock_drift_alert(monkeypatch, tmp_path):
    monkeypatch.setattr(alerts, "ALERT_PATH", tmp_path / "alerts.jsonl")
    calls = {"wall": 0, "mono": 0}

    def fake_time():
        calls["wall"] += 3
        return calls["wall"]

    def fake_monotonic():
        return calls["mono"]

    monkeypatch.setattr(cron_clock_drift.time, "time", fake_time)
    monkeypatch.setattr(cron_clock_drift.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(cron_clock_drift.time, "sleep", lambda x: None)
    drift = cron_clock_drift.check_drift()
    assert drift > 2
    data = json.loads((tmp_path / "alerts.jsonl").read_text().strip())
    assert data["type"] == "clock_drift"
