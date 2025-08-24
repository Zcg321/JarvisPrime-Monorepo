import json
from pathlib import Path
import time

from src.serve import alerts


def test_alert_severity_and_notify(tmp_path, monkeypatch):
    alert_path = tmp_path / "alerts.jsonl"
    notify_log = tmp_path / "notify.log"
    monkeypatch.setattr(alerts, "ALERT_PATH", alert_path)
    monkeypatch.setattr(alerts, "NOTIFY_LOG", notify_log)
    monkeypatch.setattr(alerts, "SUBS", [{"types": ["policy", "slo"], "notify": "log"}])

    alerts.log_event("policy", "deny")
    alerts.log_event("slo", "breach")
    time.sleep(0.01)
    recs_error = alerts.get_last(severity="ERROR")
    assert all(r["severity"] == "ERROR" for r in recs_error)
    recs_warn = alerts.get_last(severity="WARN")
    assert all(r["severity"] == "WARN" for r in recs_warn)
    assert notify_log.exists()
    lines = [json.loads(l) for l in notify_log.read_text().splitlines()]
    assert len(lines) == 2
