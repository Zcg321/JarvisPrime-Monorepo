import sys
import pathlib
import json

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from scripts import perf_harness


def test_perf_harness(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def fake_urlopen(req):
        class R:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self):
                return b"{}"
        return R()
    path = perf_harness.run("fp16", 5, 1, urlopen=fake_urlopen)
    data = json.loads(path.read_text())
    assert "p50_ms" in data and "p95_ms" in data and "tps" in data
