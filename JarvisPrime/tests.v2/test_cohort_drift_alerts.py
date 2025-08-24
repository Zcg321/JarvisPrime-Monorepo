import json
from datetime import datetime, timedelta, timezone
from src.tools import roi_cohorts
from src.serve import alerts


def test_cohort_drift_alert(tmp_path, monkeypatch):
    log = tmp_path / "roi_daily.jsonl"
    monkeypatch.setattr(roi_cohorts, "LOG_PATH", log)
    monkeypatch.setattr(alerts, "ALERT_PATH", tmp_path / "alerts.jsonl")
    now = 0
    # first 7 days
    base = datetime.now(timezone.utc) - timedelta(days=20)
    with log.open("w") as f:
        for i in range(7, 14):
            ts = (base + timedelta(days=i)).timestamp()
            rec = {"ts": ts, "slate_type": "classic", "position_bucket": "PG", "roi": 0.1}
            f.write(json.dumps(rec) + "\n")
        for i in range(14, 21):
            ts = (base + timedelta(days=i)).timestamp()
            rec = {"ts": ts, "slate_type": "classic", "position_bucket": "PG", "roi": 0.3}
            f.write(json.dumps(rec) + "\n")
    drifts = roi_cohorts.detect_drift(tau=0.05)
    assert drifts and drifts[0]["cohort"]["position_bucket"] == "PG"
    entries = alerts.get_last(10)
    assert any(r.get("type") == "cohort_drift" for r in entries)
