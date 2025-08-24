import json
from datetime import datetime, timezone, timedelta
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.serve import server_stub, metrics_store


def test_openapi_spec():
    spec = server_stub._openapi_spec()
    assert spec["info"]["config_sha"] == server_stub.CONFIG_SHA
    assert "/chat" in spec["paths"]


def test_metrics_history_pagination(tmp_path, monkeypatch):
    log = tmp_path / "rollup.jsonl"
    monkeypatch.setattr(metrics_store, "ROLLUP_LOG", log)
    now = datetime.now(timezone.utc)
    with log.open("w") as f:
        for i in range(5):
            rec = {
                "hour": (now - timedelta(hours=i)).isoformat().replace("+00:00", "Z"),
                "count": i,
                "p95_ms": 10,
            }
            f.write(json.dumps(rec) + "\n")
    rows = metrics_store.history(now - timedelta(hours=5), now)
    page1 = rows[:2]
    assert len(page1) == 2
