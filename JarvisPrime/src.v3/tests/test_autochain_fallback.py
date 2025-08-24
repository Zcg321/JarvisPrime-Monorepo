import json
import hmac
import hashlib
import os
from pathlib import Path
import sys

import requests
from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge import foreman_bridge


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def _setup(tmp_path, monkeypatch):
    (tmp_path / "foreman").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "artifacts/patches").mkdir(parents=True)
    (tmp_path / "foreman/config.yaml").write_text("models:\n  queue: dummy\n  codex: dummy\n")
    monkeypatch.setattr(foreman_bridge, "ROOT", tmp_path)
    monkeypatch.setattr(foreman_bridge, "BATON_FILE", tmp_path / "foreman/baton.json")
    monkeypatch.setattr(foreman_bridge, "REQUESTS_FILE", tmp_path / "foreman/requests.jsonl")
    monkeypatch.setattr(foreman_bridge, "LOG_FILE", tmp_path / "logs/bridge.jsonl")
    monkeypatch.setattr(foreman_bridge, "CONFIG", {"foreman_id": "jarvis-foreman", "conversation_hint": "continuum-foreman-thread"})
    foreman_bridge.METRICS.update({k:0 for k in foreman_bridge.METRICS})
    foreman_bridge.METRICS.setdefault("auto_chain", 0)
    foreman_bridge.METRICS.setdefault("planner_fallback", 0)
    foreman_bridge.CHAIN_HISTORY.clear()


def test_auto_chain_short(monkeypatch, tmp_path):
    _setup(tmp_path, monkeypatch)
    token = "t"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    monkeypatch.setenv("AUTO_CHAIN", "1")

    def fake_run(task, repo=None, branch=None):
        return {"summary":"s","next_suggestion":"Add small feature to docs section","status":"pushed","commit_or_patch":"c"}

    called = {}
    def fake_post(url, data=None, headers=None, timeout=None):
        called['body'] = data
        return type('r',(),{'status_code':200})

    monkeypatch.setattr(foreman_bridge, "run_taskcard", fake_run)
    monkeypatch.setattr(requests, "post", fake_post)

    body = {"task_card":"hi", "repo": "YOURORG/your-repo", "branch": "main"}
    raw = json.dumps(body)
    headers = {
        "X-Foreman-Id":"jarvis-foreman",
        "X-Foreman-Conv":"continuum-foreman-thread",
        "X-Foreman-Sign":_sign(raw, token)
    }
    client = TestClient(foreman_bridge.app)
    res = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert res.status_code==200
    assert foreman_bridge.METRICS['auto_chain']==1


def test_planner_fallback(monkeypatch, tmp_path):
    _setup(tmp_path, monkeypatch)
    token="t"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    monkeypatch.setenv("AUTO_CHAIN", "1")
    monkeypatch.setenv("PLANNER_FALLBACK", "1")

    def fake_run(task, repo=None, branch=None):
        return {"summary":"s","next_suggestion":"x"*500,"status":"pushed","commit_or_patch":"c"}

    def fake_planner(baton):
        return "Do follow-up work" 

    called = {}
    def fake_post(url, data=None, headers=None, timeout=None):
        called['body']=data
        return type('r',(),{'status_code':200})

    monkeypatch.setattr(foreman_bridge, "run_taskcard", fake_run)
    monkeypatch.setattr(foreman_bridge, "_planner_call", fake_planner)
    monkeypatch.setattr(requests, "post", fake_post)

    body = {"task_card":"hi", "repo": "YOURORG/your-repo", "branch": "main"}
    raw = json.dumps(body)
    headers = {
        "X-Foreman-Id":"jarvis-foreman",
        "X-Foreman-Conv":"continuum-foreman-thread",
        "X-Foreman-Sign":_sign(raw, token)
    }
    client = TestClient(foreman_bridge.app)
    res = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert res.status_code==200
    assert foreman_bridge.METRICS['planner_fallback']==1


def test_auto_chain_rate_limit(monkeypatch, tmp_path):
    _setup(tmp_path, monkeypatch)
    token="t"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    monkeypatch.setenv("AUTO_CHAIN", "1")
    monkeypatch.setenv("AUTO_CHAIN_MAX", "1")

    def fake_run(task, repo=None, branch=None):
        return {"summary":"s","next_suggestion":"Add small feature to docs section","status":"pushed","commit_or_patch":"c"}

    calls=[]
    def fake_post(url, data=None, headers=None, timeout=None):
        calls.append(data)
        return type('r',(),{'status_code':200})

    monkeypatch.setattr(foreman_bridge, "run_taskcard", fake_run)
    monkeypatch.setattr(requests, "post", fake_post)

    body={"task_card":"hi", "repo": "YOURORG/your-repo", "branch": "main"}
    raw=json.dumps(body)
    headers={"X-Foreman-Id":"jarvis-foreman","X-Foreman-Conv":"continuum-foreman-thread","X-Foreman-Sign":_sign(raw, token)}
    client=TestClient(foreman_bridge.app)
    client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert len(calls) <= 1
