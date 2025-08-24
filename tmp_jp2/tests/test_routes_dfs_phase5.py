import json
import urllib.request
import urllib.error
import pytest

NEW_TOOLS = [
    "dfs_pool",
    "dfs_exposure_solve",
    "dfs_record_result",
    "dfs_showdown",
    "ghost_dfs.seed",
    "ghost_dfs.inject",
    "dfs_calibrate",
]

def _post(port, payload):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


def test_list_tools_contains_new(server):
    res = _post(server, {"message": "list_tools"})
    for t in NEW_TOOLS:
        assert t in res["tools"]


def test_dfs_pool(server):
    res = _post(server,
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
    res = _post(server,
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
    res = _post(server,
        {
            "message": "dfs_showdown",
            "args": {"salary_cap": 50000, "max_from_team": 5, "seed": 11},
        }
    )
    assert "lineup" in res
    assert len(res["lineup"]) <= 6


def test_dfs_record_result(server):
    res = _post(server,
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
    res = _post(server, {"message": "ghost_dfs.seed", "args": {"slate_id": "LOCAL-TEST", "seed": 7, "pool_size": 4}})
    assert isinstance(res.get("pool"), list)
    assert len(res["pool"]) == 4


def test_dfs_ghost_inject(server):
    res = _post(server, {"message": "ghost_dfs.inject", "args": {"slate_id": "LOCAL-TEST", "seed": 7}})
    assert isinstance(res.get("pool"), list)
