import json
from datetime import datetime, timezone, timedelta
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import roi_cohorts


def test_roi_cohort_aggregation(tmp_path, monkeypatch):
    path = tmp_path / "roi_daily.jsonl"
    monkeypatch.setattr(roi_cohorts, "LOG_PATH", path)
    now = datetime.now(timezone.utc)
    with path.open("w") as f:
        rec1 = {"ts": now.timestamp(), "slate_type": "classic", "position_bucket": "G", "roi": 0.1}
        rec2 = {"ts": now.timestamp(), "slate_type": "classic", "position_bucket": "G", "roi": 0.2}
        f.write(json.dumps(rec1) + "\n")
        f.write(json.dumps(rec2) + "\n")
    res = roi_cohorts.roi_cohorts({"lookback_days": 30, "group_by": ["slate_type", "position_bucket"]})
    assert res[0]["cohort"] == {"slate_type": "classic", "position_bucket": "G"}
    assert res[0]["count"] == 2
    assert res[0]["p50"] == 0.1
