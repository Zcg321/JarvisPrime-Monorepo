import json
from pathlib import Path
from scripts import perf_compare


def test_perf_compare(tmp_path, monkeypatch):
    perf_dir = tmp_path / "logs/perf"
    perf_dir.mkdir(parents=True)
    (perf_dir / "a_fp16.json").write_text(json.dumps({"p50_ms": 1, "p95_ms": 2, "tps": 3, "runtime": "fp16"}))
    (perf_dir / "b_int8.json").write_text(json.dumps({"p50_ms": 2, "p95_ms": 3, "tps": 4, "runtime": "int8"}))
    monkeypatch.chdir(tmp_path)
    perf_compare.main()
    data = json.loads((perf_dir / "compare.json").read_text())
    assert data["fp16"]["p50_ms"] == 1
    assert data["int8"]["tps"] == 4
