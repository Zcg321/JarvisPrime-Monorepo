import json
from pathlib import Path
from src.serve.metrics import Metrics


def test_alerts_trigger_once(tmp_path):
    log_path = Path("logs/server.log")
    if log_path.exists():
        log_path.unlink()
    m = Metrics()
    m.thresholds = {"avg_latency_ms_fp16": 1}
    m.record(2, "fp16", False)
    lines = [json.loads(l) for l in log_path.read_text().splitlines()]
    assert any(l.get("level") == "ALERT" for l in lines)
    assert m.alerts_total == 1
    m.record(3, "fp16", False)
    lines = [json.loads(l) for l in log_path.read_text().splitlines()]
    assert sum(1 for l in lines if l.get("level") == "ALERT") == 1
    assert m.alerts_total == 1
