import asyncio
from pathlib import Path
import sys
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge.worker_pool import WorkerPool


class Err(Exception):
    def __init__(self, status):
        self.status = status


def test_backoff_and_metrics(monkeypatch):
    attempts = {"n": 0}

    async def fake_run(task, repo=None, branch=None):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise Err(429)
        return {"status": "pushed"}

    monkeypatch.setattr("bridge.worker_pool.run_taskcard_async", fake_run)
    async def fast_sleep(x):
        return
    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    cfg = {"pool": {"max_workers": 1, "rate_limits": {"backoff_initial_ms": 1, "backoff_max_ms": 2}}}
    pool = WorkerPool(cfg)

    async def run_test():
        pool.start()
        pool.enqueue("A", "r1", None)
        await asyncio.sleep(0.05)
        assert pool.metrics["codex_429_total"] == 1
        assert attempts["n"] == 2
    asyncio.run(run_test())
    asyncio.run(pool.shutdown())
