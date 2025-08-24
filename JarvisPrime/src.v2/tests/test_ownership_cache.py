import time
import importlib
import time
from pathlib import Path
from threading import Thread

import pytest

def _write(p, val):
    p.write_text("player_id,team,proj_points,field_own_pct\n" + val)


def test_ttl_and_mtime(tmp_path, monkeypatch):
    monkeypatch.setenv("OWNERSHIP_TTL_S", "1")
    import src.data.ownership as ownership
    importlib.reload(ownership)
    p = tmp_path / "own.csv"
    _write(p, "p1,A,10,0.1\n")
    r1 = ownership.load_daily(p)
    time.sleep(1.2)
    r2 = ownership.load_daily(p)
    assert r1 is not r2
    _write(p, "p1,A,12,0.1\n")
    r3 = ownership.load_daily(p)
    assert r2 is not r3


def test_concurrency_single_load(tmp_path, monkeypatch):
    monkeypatch.setenv("OWNERSHIP_TTL_S", "300")
    import src.data.ownership as ownership
    importlib.reload(ownership)
    p = tmp_path / "own.csv"
    _write(p, "p1,A,10,0.1\n")
    calls = []
    orig_open = Path.open

    def spy_open(self, *a, **k):
        calls.append(1)
        return orig_open(self, *a, **k)

    monkeypatch.setattr(Path, "open", spy_open)
    results = []
    def load():
        results.append(ownership.load_daily(p))
    threads = [Thread(target=load) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(calls) == 1
    assert all(r is results[0] for r in results)
