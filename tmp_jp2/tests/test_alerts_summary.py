import json, time, urllib.request
from pathlib import Path
from src.serve import alerts

ADMIN = {"Authorization": "Bearer ADMIN_TOKEN"}


def test_alerts_ttl_and_summary(tmp_path, monkeypatch):
    alert_path = tmp_path / "alerts.jsonl"
    monkeypatch.setattr(alerts, "ALERT_PATH", alert_path)
    old = time.time() - 40 * 86400
    new = time.time()
    alert_path.write_text(
        json.dumps({"ts": old, "type": "slo", "severity": "ERROR"}) + "\n" +
        json.dumps({"ts": new, "type": "policy", "severity": "WARN"}) + "\n"
    )
    summary = alerts.summary()
    assert summary["severity"]["ERROR"] == 0
    assert summary["severity"]["WARN"] == 1
    assert len(alert_path.read_text().splitlines()) == 1


def test_alerts_summary_endpoint(server):
    port = server
    req = urllib.request.Request(f"http://127.0.0.1:{port}/alerts/summary", headers=ADMIN)
    data = json.loads(urllib.request.urlopen(req).read())
    assert "severity" in data and "type" in data
