import json
import hmac
import hashlib
import hmac
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge import foreman_bridge


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def setup_app(tmp_path, monkeypatch):
    (tmp_path / "foreman").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "foreman/requests.jsonl").write_text("")
    (tmp_path / "foreman/config.yaml").write_text("models:\n  codex: dummy\nmax_files_touched: 15\n")
    monkeypatch.setattr(foreman_bridge, "ROOT", tmp_path)
    monkeypatch.setattr(foreman_bridge, "BATON_FILE", tmp_path / "foreman/baton.json")
    monkeypatch.setattr(foreman_bridge, "REQUESTS_FILE", tmp_path / "foreman/requests.jsonl")
    monkeypatch.setattr(foreman_bridge, "LOG_FILE", tmp_path / "logs/bridge.jsonl")
    monkeypatch.setattr(
        foreman_bridge,
        "CONFIG",
        {"foreman_id": "jarvis-foreman", "conversation_hint": "continuum-foreman-thread"},
    )
    monkeypatch.setattr(foreman_bridge, "ANCHORS", [])
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", "secret")
    foreman_bridge.METRICS.update({
        "workers_busy": 0,
        "queue_depth": 0,
        "queue_depth_by_priority": {0: 0, 1: 0, 2: 0},
        "idempotent_hits": 0,
        "auto_chain": 0,
        "planner_fallback": 0,
        "rate_limited": 0,
    })
    foreman_bridge.METRICS.setdefault("rate_limited", 0)


def test_idempotency_and_rate_limit(tmp_path, monkeypatch):
    def dummy_run(task):
        return {
            "summary": "ok",
            "next_suggestion": "",
            "status": "pushed",
            "commit_or_patch": "abc",
        }

    monkeypatch.setattr(foreman_bridge, "run_taskcard", lambda task, repo=None, branch=None: dummy_run(task))
    setup_app(tmp_path, monkeypatch)
    client = TestClient(foreman_bridge.app)

    body = {"task_card": "hi", "repo": "YOURORG/your-repo", "branch": "main"}
    raw = json.dumps(body)
    headers = {
        "Content-Type": "application/json",
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(raw, "secret"),
        "X-Idempotency-Key": "abc",
    }

    res1 = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert res1.status_code == 200
    res2 = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert res2.status_code == 200

