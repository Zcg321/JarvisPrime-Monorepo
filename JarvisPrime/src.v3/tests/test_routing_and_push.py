import json
import hmac
import hashlib
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
import yaml

sys.path.append(str(Path(__file__).resolve().parents[1]))
from bridge import foreman_bridge


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def test_policy_and_explicit_routing(tmp_path, monkeypatch):
    root = tmp_path
    (root / "foreman").mkdir()
    (root / "foreman/config.yaml").write_text(
        "foreman_id: jarvis-foreman\nconversation_hint: continuum-foreman-thread\nrouting:\n  policies:\n    docs: { repo: \"YOURORG/docs\", branch: \"main\" }\n  default: { repo: \"YOURORG/your-repo\", branch: \"main\" }\nrepos:\n  YOURORG/docs: { branch: main, token_env: GT_TOKEN }\n  YOURORG/your-repo: { branch: main, token_env: GT_TOKEN }\n"
    )
    monkeypatch.setattr(foreman_bridge, "ROOT", root)
    cfg = yaml.safe_load((root / "foreman/config.yaml").read_text())
    monkeypatch.setattr(foreman_bridge, "CONFIG", cfg)
    monkeypatch.setattr(foreman_bridge, "BATON_FILE", root / "foreman/baton.json")
    monkeypatch.setattr(foreman_bridge, "REQUESTS_FILE", root / "foreman/requests.jsonl")
    monkeypatch.setattr(foreman_bridge, "LOG_FILE", root / "logs/bridge.jsonl")
    (root / "logs").mkdir()
    (root / "foreman/requests.jsonl").write_text("")
    foreman_bridge.METRICS.update({k: 0 for k in foreman_bridge.METRICS})
    captured = []

    def fake_run(task, repo=None, branch=None):
        captured.append((repo, branch))
        baton = {"summary": "", "next_suggestion": "", "status": "pushed", "last_commit": "c", "updated": "now", "context_bytes": 1}
        (root / "foreman/baton.json").write_text(json.dumps(baton))
        return {"summary": "", "next_suggestion": "", "status": "pushed", "commit_or_patch": "c", "remote_mode": "https"}

    monkeypatch.setattr(foreman_bridge, "run_taskcard", fake_run)

    token = "tok"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    client = TestClient(foreman_bridge.app)

    body = {"task_card": "hello", "policy_key": "docs"}
    raw = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(raw, token),
    }
    res = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert res.status_code == 200
    assert captured[-1] == ("YOURORG/docs", "main")

    body = {"task_card": "hi", "repo": "YOURORG/your-repo", "branch": "main"}
    raw = json.dumps(body)
    headers["X-Foreman-Sign"] = _sign(raw, token)
    res = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    assert res.status_code == 200
    assert captured[-1] == ("YOURORG/your-repo", "main")
