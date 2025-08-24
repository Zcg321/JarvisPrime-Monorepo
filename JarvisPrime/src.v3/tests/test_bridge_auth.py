import json
import hmac
import hashlib
from pathlib import Path
import sys
import hmac
import hashlib
import json

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge import foreman_bridge


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(foreman_bridge, "REQUESTS_FILE", tmp_path / "requests.jsonl")
    monkeypatch.setattr(foreman_bridge, "LOG_FILE", tmp_path / "bridge.jsonl")
    monkeypatch.setattr(
        foreman_bridge,
        "CONFIG",
        {"foreman_id": "jarvis-foreman", "conversation_hint": "continuum-foreman-thread"},
    )
    foreman_bridge.METRICS.update({
        "workers_busy": 0,
        "queue_depth": 0,
        "queue_depth_by_priority": {0: 0, 1: 0, 2: 0},
        "idempotent_hits": 0,
        "auto_chain": 0,
        "planner_fallback": 0,
        "rate_limited": 0,
    })


def test_auth_success(tmp_path, monkeypatch):
    token = "secret"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    _setup(tmp_path, monkeypatch)
    body = {"task_card": "hello", "repo": "YOURORG/your-repo", "branch": "main"}
    data = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(data, token),
    }
    monkeypatch.setattr(
        foreman_bridge,
        "run_taskcard",
        lambda tc, repo=None, branch=None: {"summary": "", "next_suggestion": "", "status": "pushed", "commit_or_patch": ""},
    )
    client = TestClient(foreman_bridge.app)
    res = client.post("/v1/taskcards?sync=1", data=data, headers=headers)
    assert res.status_code == 200


def test_auth_bad_sig(tmp_path, monkeypatch):
    token = "secret"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    _setup(tmp_path, monkeypatch)
    body = {"task_card": "hello", "repo": "YOURORG/your-repo", "branch": "main"}
    data = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": "bad",
    }
    client = TestClient(foreman_bridge.app)
    res = client.post("/v1/taskcards", data=data, headers=headers)
    assert res.status_code == 403


def test_queue_public(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    client = TestClient(foreman_bridge.app)
    res = client.get("/v1/queue")
    assert res.status_code == 200


def test_cancel_requires_auth(tmp_path, monkeypatch):
    token = "secret"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    _setup(tmp_path, monkeypatch)
    body = {"task_card": "hello", "repo": "YOURORG/your-repo", "branch": "main"}
    data = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(data, token),
    }
    client = TestClient(foreman_bridge.app)
    res = client.post("/v1/taskcards", data=data, headers=headers)
    tid = res.json()["task_id"]
    # cancel without auth
    res2 = client.post("/v1/taskcards/cancel", json={"task_id": tid})
    assert res2.status_code == 403


def test_auth_reserialized_body(tmp_path, monkeypatch):
    token = "secret"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    _setup(tmp_path, monkeypatch)
    body = {"task_card": "hello", "repo": "YOURORG/your-repo", "branch": "main"}
    signed = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(signed, token),
    }
    client = TestClient(foreman_bridge.app)
    res = client.post("/v1/taskcards", json=body, headers=headers)
    assert res.status_code == 403
