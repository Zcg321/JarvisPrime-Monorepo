import json
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import dfs_exposure


def test_pool_and_exposure(monkeypatch):
    def fake_seed_pool(slate_id, seed, pool_size=10):
        return [
            {
                "lineup_id": "L0",
                "players": [
                    {"player": "A", "team": "T1"},
                    {"player": "B", "team": "T2"},
                ],
                "salary_total": 40000,
                "leftover": 10000,
            },
            {
                "lineup_id": "L1",
                "players": [
                    {"player": "A", "team": "T1"},
                    {"player": "C", "team": "T2"},
                ],
                "salary_total": 40000,
                "leftover": 10000,
            },
            {
                "lineup_id": "L2",
                "players": [
                    {"player": "D", "team": "T3"},
                    {"player": "E", "team": "T4"},
                ],
                "salary_total": 40000,
                "leftover": 10000,
            },
        ]
    monkeypatch.setattr(dfs_exposure, "ghost_dfs", type("x", (), {"seed_pool": fake_seed_pool}))
    res = dfs_exposure.solve("SLATE", n_lineups=2, max_from_team=2, global_exposure_caps={"A": 0.5}, seed=1)
    if res["lineups"]:
        count = sum(any(p["player"] == "A" for p in lu["players"]) for lu in res["lineups"])
        assert count / len(res["lineups"]) <= 0.5
