import sys, pathlib
import json

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import dfs_exposure


def fake_seed_pool(slate_id, seed, pool_size=10):
    return [
        {
            "lineup_id": "L0",
            "players": [
                {"player": "A", "team": "T1"},
                {"player": "B", "team": "T1"},
                {"player": "C", "team": "T2"},
            ],
            "salary_total": 30000,
            "leftover": 20000,
        },
        {
            "lineup_id": "L1",
            "players": [
                {"player": "A", "team": "T1"},
                {"player": "D", "team": "T2"},
                {"player": "E", "team": "T3"},
            ],
            "salary_total": 30000,
            "leftover": 20000,
        },
        {
            "lineup_id": "L2",
            "players": [
                {"player": "F", "team": "T3"},
                {"player": "G", "team": "T3"},
                {"player": "H", "team": "T3"},
            ],
            "salary_total": 30000,
            "leftover": 20000,
        },
        {
            "lineup_id": "L3",
            "players": [
                {"player": "I", "team": "T4"},
                {"player": "J", "team": "T5"},
                {"player": "K", "team": "T6"},
            ],
            "salary_total": 30000,
            "leftover": 20000,
        },
    ]


def test_exposure_solver(monkeypatch):
    monkeypatch.setattr(dfs_exposure, "ghost_dfs", type("x", (), {"seed_pool": fake_seed_pool}))
    res = dfs_exposure.solve(
        "SLATE",
        n_lineups=2,
        max_from_team=2,
        global_exposure_caps={"A": 0.5},
        seed=1,
    )
    assert len(res["lineups"]) == 2
    exposure = res["exposure"]
    assert exposure["A"] <= 0.5
    for lu in res["lineups"]:
        counts = {}
        for p in lu["players"]:
            counts[p["team"]] = counts.get(p["team"], 0) + 1
        assert max(counts.values()) <= 2
    # deterministic
    res2 = dfs_exposure.solve(
        "SLATE",
        n_lineups=2,
        max_from_team=2,
        global_exposure_caps={"A": 0.5},
        seed=1,
    )
    assert res == res2
