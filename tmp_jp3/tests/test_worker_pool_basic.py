import asyncio
import time
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge.worker_pool import WorkerPool


def test_concurrency_and_repo_lock(monkeypatch):
    calls = []

    async def fake_run(task, repo=None, branch=None):
        calls.append((task, repo, branch, time.time()))
        await asyncio.sleep(0.1)
        return {"status": "pushed"}

    monkeypatch.setattr("bridge.worker_pool.run_taskcard_async", fake_run)
    cfg = {"pool": {"max_workers": 2, "max_per_repo": 1}}
    pool = WorkerPool(cfg)
    async def run_test():
        pool.start()
        pool.enqueue("A", "r1", None)
        pool.enqueue("B", "r2", None)
        await asyncio.sleep(0.15)
        assert len(calls) == 2
        calls.clear()
        pool.enqueue("C", "r3", None)
        pool.enqueue("D", "r3", None)
        await asyncio.sleep(0.25)
        assert calls[0][3] + 0.09 <= calls[1][3]
    asyncio.run(run_test())
    asyncio.run(pool.shutdown())


def test_branch_isolation(monkeypatch):
    async def fake_run(task, repo=None, branch=None):
        await asyncio.sleep(0.05)
        return {"status": "pushed"}

    monkeypatch.setattr("bridge.worker_pool.run_taskcard_async", fake_run)
    cfg = {"pool": {"max_workers": 2, "max_per_repo": 2}, "branching": {"enable_isolation": True}}
    pool = WorkerPool(cfg)
    async def run_test():
        pool.start()
        pool.enqueue("A", "rX", None)
        pool.enqueue("B", "rX", None)
        await asyncio.sleep(0.1)
        assert pool.metrics["tasks_completed"] >= 2
    asyncio.run(run_test())
    asyncio.run(pool.shutdown())
