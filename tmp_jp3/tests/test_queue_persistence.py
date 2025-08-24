import asyncio
import os
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge.worker_pool import WorkerPool


def test_queue_persistence(tmp_path, monkeypatch):
    root = Path('foreman')
    for f in ['queue.jsonl', 'dlq.jsonl']:
        try:
            (root / f).unlink()
        except FileNotFoundError:
            pass
    calls = []

    failures = set()

    async def fake_run(task, repo=None, branch=None):
        if 'fail' in task and task not in failures:
            failures.add(task)
            raise RuntimeError('boom')
        calls.append(task)
        return {"status": "pushed"}

    monkeypatch.setattr('bridge.worker_pool.run_taskcard_async', fake_run)
    cfg = {"pool": {"max_workers": 1, "max_retries": 1}}
    pool1 = WorkerPool(cfg)
    ok_item, _, _ = pool1.enqueue('ok', None, None)
    bad_item, _, _ = pool1.enqueue('fail', None, None)
    # simulate restart
    pool2 = WorkerPool(cfg)
    assert sum(len(q) for q in pool2.queues.values()) == 2

    async def run():
        pool2.start()
        for _ in range(50):
            if pool2.metrics['tasks_completed'] + pool2.metrics['tasks_failed'] >= 2:
                break
            await asyncio.sleep(0.1)
        await pool2.shutdown()
    asyncio.run(run())

    dlq = pool2.store.dlq_summary()
    assert bad_item.id in dlq
    # requeue and process again
    pool2.store.requeue(bad_item.id)
    pool3 = WorkerPool(cfg)
    async def run2():
        pool3.start()
        for _ in range(50):
            if pool3.metrics['tasks_completed'] >= 2:
                break
            await asyncio.sleep(0.1)
        await pool3.shutdown()
    asyncio.run(run2())
    assert pool3.store.dlq_summary() == {}
