import asyncio
import json
import hmac
import hashlib
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import time
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge import foreman_bridge
from bridge.worker_pool import WorkerPool


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def test_shutdown_endpoint(tmp_path, monkeypatch):
    root = tmp_path
    (root / "foreman").mkdir()
    (root / "foreman/config.yaml").write_text("foreman_id: jarvis-foreman\nconversation_hint: continuum-foreman-thread\n")
    monkeypatch.setattr(foreman_bridge, "ROOT", root)
    import yaml
    monkeypatch.setattr(foreman_bridge, "CONFIG", yaml.safe_load((root / "foreman/config.yaml").read_text()))
    pool = WorkerPool({"pool": {"max_workers": 2}})
    monkeypatch.setattr(foreman_bridge, "POOL", pool)
    monkeypatch.setattr(foreman_bridge, "BATON_FILE", root / "foreman/baton.json")
    monkeypatch.setattr(foreman_bridge, "REQUESTS_FILE", root / "foreman/requests.jsonl")
    monkeypatch.setattr(foreman_bridge, "LOG_FILE", root / "logs/bridge.jsonl")
    (root / "foreman/requests.jsonl").write_text("")
    (root / "logs").mkdir()
    async def fake_run(task, repo=None, branch=None):
        await asyncio.sleep(0.1)
        return {"status": "pushed", "remote_mode": "https"}

    monkeypatch.setattr("bridge.worker_pool.run_taskcard_async", fake_run)

    token = "tok"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    client = TestClient(foreman_bridge.app)

    body = {"task_card": "a", "repo": "YOURORG/your-repo", "branch": "main"}
    raw = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(raw, token),
    }
    client.post("/v1/taskcards", data=raw, headers=headers)
    time.sleep(0.2)
    shut_headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign("", token),
    }
    res = client.post("/v1/admin/shutdown", data="", headers=shut_headers)
    assert res.status_code == 200
    body = res.json()
    assert body.get("stopped") is True
    assert pool.workers == []
