import asyncio
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge.worker_pool import WorkerPool


def test_priority_and_dedupe(monkeypatch):
    calls = []

    async def fake_run(task, repo=None, branch=None):
        calls.append((task, branch, time.time()))
        await asyncio.sleep(0.05)
        return {"status": "pushed"}

    monkeypatch.setattr("bridge.worker_pool.run_taskcard_async", fake_run)
    cfg = {"pool": {"max_workers": 1}}
    pool = WorkerPool(cfg)

    async def run_test():
        item1, acc1, pos1 = pool.enqueue("X", None, None)
        item2, acc2, pos2 = pool.enqueue("X", None, None)
        assert not acc2 and item1.id == item2.id
        pool.enqueue("low", None, None, priority=2)
        pool.enqueue("high", None, None, priority=0)
        pool.start()
        for _ in range(40):
            if len(calls) >= 3:
                break
            await asyncio.sleep(0.05)
        assert len(calls) >= 3
        names = [c[0] for c in calls if c[0] != "X"]
        assert names[0] == "high" and names[1] == "low"
    asyncio.run(run_test())
    asyncio.run(pool.shutdown())
