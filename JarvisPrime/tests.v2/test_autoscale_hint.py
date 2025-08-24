import json
from datetime import datetime, timezone
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.serve import autoscale


def test_autoscale_hint(tmp_path, monkeypatch):
    roll = tmp_path / "rollup.jsonl"
    monkeypatch.setattr(autoscale, "ROLLUP_PATH", roll)
    monkeypatch.setattr(autoscale, "CFG", {"up": {"rps": 5, "p95_ms": 100}, "down": {"rps": 1, "p95_ms": 50}})
    now = datetime.now(timezone.utc)
    with roll.open("w") as f:
        f.write(json.dumps({"hour": now.isoformat(), "count": 600, "p95_ms": 150}) + "\n")
    assert autoscale.hint()["scale"] == "up"
    with roll.open("w") as f:
        f.write(json.dumps({"hour": now.isoformat(), "count": 30, "p95_ms": 30}) + "\n")
    assert autoscale.hint()["scale"] == "down"
