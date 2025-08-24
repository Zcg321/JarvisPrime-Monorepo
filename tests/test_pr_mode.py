import asyncio
import json
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge.worker_pool import WorkerPool, BATON_FILE


def test_pr_mode(monkeypatch, tmp_path):
    baton_file = tmp_path / "baton.json"
    monkeypatch.setattr("bridge.worker_pool.BATON_FILE", baton_file)

    async def fake_run(task, repo=None, branch=None):
        assert branch.startswith("autofeature/")
        baton_file.write_text(json.dumps({"pr_url": "https://pr"}))
        return {"status": "pushed", "remote_mode": "https", "pr_url": "https://pr"}

    monkeypatch.setattr("bridge.worker_pool.run_taskcard_async", fake_run)
    cfg = {"pool": {"max_workers": 1}, "repos": {"YOURORG/alchohalt": {"branch": "main", "pr_mode": True}}}
    pool = WorkerPool(cfg)

    async def run_test():
        pool.start()
        pool.enqueue("do it", "YOURORG/alchohalt", None)
        for _ in range(40):
            if pool.metrics["tasks_completed"] >= 1:
                break
            await asyncio.sleep(0.05)
    asyncio.run(run_test())
    asyncio.run(pool.shutdown())
    data = json.loads(baton_file.read_text())
    assert data.get("pr_url") == "https://pr"
