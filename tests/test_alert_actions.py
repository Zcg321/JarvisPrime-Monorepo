import json
from pathlib import Path
from src.serve import alerts
from src.savepoint import logger as splog


def test_error_alert_savepoint_and_escalation(tmp_path, monkeypatch):
    alert_path = tmp_path / "alerts.jsonl"
    save_dir = tmp_path / "sps"
    monkeypatch.setattr(alerts, "ALERT_PATH", alert_path)
    monkeypatch.setattr(splog, "LOG_DIR", save_dir)
    # first error generates savepoint
    alerts.log_event("slo", "breach")
    files = list(save_dir.glob("*.json"))
    assert len(files) == 1
    # trigger escalation after more errors
    for i in range(6):
        alerts.log_event("slo", f"breach {i}")
    lines = [json.loads(l) for l in alert_path.read_text().splitlines()]
    assert any(r.get("type") == "escalation" for r in lines)
