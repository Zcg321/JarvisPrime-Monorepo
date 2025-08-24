import json
from pathlib import Path

from src.serve import alerts
from src.serve import logging as slog


def test_alert_logging_severity(tmp_path, monkeypatch):
    log_path = tmp_path / 'server.log'
    monkeypatch.setattr(slog, 'LOG_PATH', log_path)
    monkeypatch.setattr(alerts, 'ALERT_PATH', tmp_path / 'alerts.jsonl')
    monkeypatch.setattr(alerts, 'NOTIFY_LOG', tmp_path / 'notify.log')
    monkeypatch.setattr(alerts, 'SUBS', [{"types": ["policy"], "notify": "log"}])
    alerts.log_event('policy', 'deny')
    rec = json.loads(log_path.read_text().splitlines()[0])
    assert rec['level'] == 'ALERT'
    assert rec['severity'] == 'WARN'
    assert rec['notify'] == 'log'
