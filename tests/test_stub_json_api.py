import json
import subprocess
import time
import urllib.request
import pytest

CANONICAL = [
    "dfs_pool",
    "dfs_exposure_solve",
    "dfs_record_result",
    "dfs_showdown",
    "dfs_ghost_seed",
    "dfs_ghost_inject",
    "dfs_calibrate",
    "surgecell_apply",
    "voice_mirror_reflect",
    "dfs_lineup",
    "dfs_roi",
    "savepoint_write",
    "savepoint_list",
    "uptake_record",
    "uptake_replay",
    "uptake_search",
    "uptake_stats",
    "reflex_decide",
    "context_search",
    "plan_query",
]

@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(["python", "-m", "src.serve.server_stub"])
    for _ in range(20):
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=0.2):
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("server did not start")
    yield
    proc.terminate()
    proc.wait(timeout=5)


def _post(payload):
    req = urllib.request.Request(
        "http://127.0.0.1:8000/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def test_list_tools(server):
    res = _post({"message": "list_tools"})
    assert res["tools"] == CANONICAL


def test_kill_phrase(server):
    res = _post({"message": "lights out, jarvis"})
    assert res == {"status": "standby"}


def test_dfs_roi(server):
    res = _post({
        "message": "dfs_roi",
        "args": {"entry_fees": [20, 20, 20], "winnings": [0, 40, 100]},
    })
    assert res["total_fee"] == 60
    assert res["total_win"] == 140
    assert res["net"] == 80
    assert round(res["roi_pct"], 2) == 133.33


def test_savepoint_cycle(server):
    res = _post({"message": "savepoint_write", "args": {"moment": "test"}})
    assert res.get("ok")
    res2 = _post({"message": "savepoint_list", "args": {"n": 5}})
    assert any(sp.get("moment") == "test" for sp in res2["savepoints"])
