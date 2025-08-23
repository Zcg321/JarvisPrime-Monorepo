import json
import subprocess
import time
import urllib.request
import pytest

NEW_TOOLS = [
    "dfs_pool",
    "dfs_exposure_solve",
    "dfs_record_result",
    "dfs_showdown",
    "dfs_ghost_seed",
    "dfs_ghost_inject",
    "dfs_calibrate",
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


def test_list_tools_contains_new(server):
    res = _post({"message": "list_tools"})
    for t in NEW_TOOLS:
        assert t in res["tools"]


def test_dfs_pool(server):
    res = _post(
        {
            "message": "dfs_pool",
            "args": {
                "source": "mock",
                "N": 5,
                "salary_cap": 50000,
                "roster_slots": {"PG": 2, "SG": 2, "SF": 2, "PF": 2, "C": 1},
                "max_from_team": 3,
                "seed": 7,
            },
        }
    )
    assert isinstance(res.get("pool"), list)
    assert len(res["pool"]) == 5


def test_dfs_exposure(server):
    res = _post(
        {
            "message": "dfs_exposure_solve",
            "args": {
                "target_size": 5,
                "per_player_max_pct": 0.6,
                "team_max": 3,
                "diversity_lambda": 0.1,
                "seed": 7,
            },
        }
    )
    assert isinstance(res.get("lineups"), list)
    assert len(res["lineups"]) == 5


def test_dfs_showdown(server):
    res = _post(
        {
            "message": "dfs_showdown",
            "args": {"salary_cap": 50000, "max_from_team": 5, "seed": 11},
        }
    )
    assert "lineup" in res
    assert len(res["lineup"]) <= 6


def test_dfs_record_result(server):
    res = _post(
        {
            "message": "dfs_record_result",
            "args": {
                "slate_id": "LOCAL-TEST",
                "entry_fee": 100,
                "winnings": 150,
                "lineup_signature": "auto",
            },
        }
    )
    assert "roi" in res and res["roi"] == pytest.approx(0.5)


def test_dfs_ghost_seed(server):
    res = _post(
        {
            "message": "dfs_ghost_seed",
            "args": {"lineups_from": "pool_top", "k": 4, "slate_id": "LOCAL-TEST"},
        }
    )
    assert res.get("seeded") == 4


def test_dfs_ghost_inject(server):
    res = _post(
        {
            "message": "dfs_ghost_inject",
            "args": {
                "k": 3,
                "mutate_rate": 0.1,
                "salary_cap": 50000,
                "roster_slots": {"PG": 2, "SG": 2, "SF": 2, "PF": 2, "C": 1},
                "max_from_team": 3,
                "seed": 19,
            },
        }
    )
    assert isinstance(res.get("ghosts"), list)
    assert len(res["ghosts"]) == 3
