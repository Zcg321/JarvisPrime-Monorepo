import json
import os
import subprocess
import hmac
import hashlib
import sys
import json
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from bridge import foreman_bridge
from duet import duet_foreman


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def test_baton_roundtrip(tmp_path, monkeypatch):
    root = tmp_path
    (root / "foreman").mkdir()
    (root / "artifacts/patches").mkdir(parents=True)
    (root / "foreman/config.yaml").write_text("models:\n  codex: dummy\nmax_files_touched: 15\n")

    monkeypatch.setattr(duet_foreman, "ROOT", root)
    monkeypatch.setattr(duet_foreman, "FOREMAN", root / "foreman")
    monkeypatch.setattr(duet_foreman, "BATON_FILE", root / "foreman/baton.json")
    monkeypatch.setattr(duet_foreman, "ARTIFACTS", root / "artifacts")
    monkeypatch.setattr(duet_foreman, "PATCHES", root / "artifacts/patches")

    monkeypatch.setattr(foreman_bridge, "ROOT", root)
    monkeypatch.setattr(foreman_bridge, "BATON_FILE", root / "foreman/baton.json")
    monkeypatch.setattr(
        foreman_bridge,
        "CONFIG",
        {"foreman_id": "jarvis-foreman", "conversation_hint": "continuum-foreman-thread"},
    )
    monkeypatch.setattr(foreman_bridge, "ANCHORS", [])
    monkeypatch.setattr(foreman_bridge, "REQUESTS_FILE", root / "foreman/requests.jsonl")
    monkeypatch.setattr(foreman_bridge, "LOG_FILE", root / "logs/bridge.jsonl")
    (root / "foreman/requests.jsonl").write_text("")
    (root / "logs").mkdir()
    foreman_bridge.METRICS.update({k: 0 for k in foreman_bridge.METRICS})

    def fake_run(task, repo=None, branch=None):
        baton = {
            "summary": "done",
            "next_suggestion": "next",
            "status": "pushed",
            "last_commit": "abc123",
            "updated": "now",
            "context_bytes": 10,
            "remote_mode": "https",
        }
        (root / "foreman/baton.json").write_text(json.dumps(baton))
        return {
            "summary": "done",
            "next_suggestion": "next",
            "status": "pushed",
            "commit_or_patch": "abc123",
            "remote_mode": "https",
        }

    monkeypatch.setattr(foreman_bridge, "run_taskcard", fake_run)

    subprocess.run(["git", "init"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "bot@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "bot"], cwd=root, check=True)
    (root / "seed.txt").write_text("seed")
    subprocess.run(["git", "add", "seed.txt"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True)

    token = "secret"
    monkeypatch.setenv("FOREMAN_SHARED_TOKEN", token)
    body = {"task_card": "hello", "repo": "YOURORG/your-repo", "branch": "main"}
    raw = json.dumps(body)
    headers = {
        "X-Foreman-Id": "jarvis-foreman",
        "X-Foreman-Conv": "continuum-foreman-thread",
        "X-Foreman-Sign": _sign(raw, token),
    }
    client = TestClient(foreman_bridge.app)

    cwd = os.getcwd()
    os.chdir(root)
    try:
        res = client.post("/v1/taskcards?sync=1", data=raw, headers=headers)
    finally:
        os.chdir(cwd)

    assert res.status_code == 200
    baton = json.loads((root / "foreman/baton.json").read_text())
    assert baton["summary"] == "done"
    assert baton["next_suggestion"] == "next"
    assert baton["status"] in {"pushed", "patched"}
    assert baton["repo"] == "YOURORG/your-repo"
    assert baton["branch"] == "main"
    assert "task_id" in baton
    assert baton["context_bytes"] == 10
    assert baton["remote_mode"] == "https"
    resp = res.json()
    if baton["status"] == "pushed":
        assert "last_commit" in baton
        assert resp["commit_or_patch"] == baton["last_commit"]
    else:
        assert "last_patch" in baton
        assert resp["commit_or_patch"] == baton["last_patch"]

    # metrics updated
    m = client.get("/v1/metrics").json()["metrics"]
    assert m["tasks_completed"] == 1

    # log entry written
    log_lines = (root / "logs/bridge.jsonl").read_text().splitlines()
    assert len(log_lines) == 1
    rec = json.loads(log_lines[0])
    assert rec["result"] == "pushed"
