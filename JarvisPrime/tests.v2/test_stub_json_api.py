import json
import urllib.request
import pytest

CANONICAL = [
    "dfs_pool",
    "dfs_exposure_solve",
    "dfs_portfolio",
    "dfs_record_result",
    "dfs_showdown",
    "dfs_calibrate",
    "slate_sim",
    "roi_report",
    "results_ingest",
    "bankroll_alloc",
    "portfolio_eval",
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
    "surgecell",
    "voice_mirror",
    "savepoint",
    "dfs",
    "ghost_dfs.seed",
    "ghost_dfs.inject",
    "ghost_dfs",
    "traid_signal",
    "reflex",
    "schedule_query",
    "validate_inputs",
]

def _post(port, payload):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def test_list_tools(server):
    res = _post(server, {"message": "list_tools"})
    assert "submit_plan" in res["tools"]


def test_kill_phrase(server):
    res = _post(server, {"message": "lights out, jarvis"})
    assert res == {"status": "standby"}


def test_dfs_roi(server):
    res = _post(server, {
        "message": "dfs_roi",
        "args": {"entry_fees": [20, 20, 20], "winnings": [0, 40, 100]},
    })
    assert res["total_fee"] == 60
    assert res["total_win"] == 140
    assert res["net"] == 80
    assert round(res["roi_pct"], 2) == 133.33


def test_savepoint_cycle(server):
    res = _post(server, {"message": "savepoint_write", "args": {"event": "test", "payload": {"x": 1}}})
    assert res.get("path")
    res2 = _post(server, {"message": "savepoint_list", "args": {"n": 5}})
    assert any(sp.get("event") == "test" for sp in res2["savepoints"])
