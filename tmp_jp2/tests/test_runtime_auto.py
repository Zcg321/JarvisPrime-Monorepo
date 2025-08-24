import json
from src.serve import runtime_auto


def test_decide_runtime_from_logs(tmp_path):
    data = {"fp16": {"p95_ms": 100}, "int8": {"p95_ms": 120}}
    p = tmp_path / "compare.json"
    p.write_text(json.dumps(data))
    assert runtime_auto.decide_runtime_from_logs(str(p)) == "fp16"
