import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import dfs

PLAYERS = [
    {"name": "QB1", "pos": "QB", "cost": 15, "proj": 18},
    {"name": "QB2", "pos": "QB", "cost": 12, "proj": 16},
    {"name": "RB1", "pos": "RB", "cost": 10, "proj": 15},
    {"name": "RB2", "pos": "RB", "cost": 11, "proj": 16},
    {"name": "RB3", "pos": "RB", "cost": 9, "proj": 14},
    {"name": "WR1", "pos": "WR", "cost": 8, "proj": 13},
    {"name": "WR2", "pos": "WR", "cost": 9, "proj": 14},
    {"name": "WR3", "pos": "WR", "cost": 10, "proj": 15},
    {"name": "WR4", "pos": "WR", "cost": 7, "proj": 11},
    {"name": "TE1", "pos": "TE", "cost": 5, "proj": 8},
]

def test_positional_lineup():
    res = dfs.predict_lineup(PLAYERS, budget=60)
    assert res["cost"] == 60
    assert res["expected"] == 91
    assert res["remaining_budget"] == 0
    assert res["complete"] is True
    counts = {}
    for p in res["lineup"]:
        counts[p["pos"]] = counts.get(p["pos"], 0) + 1
    assert counts["QB"] == 1
    assert counts["RB"] == 2
    assert counts["WR"] == 3
    # FLEX filled with TE1
    assert counts.get("TE", 0) == 1
    assert len(res["lineup"]) == 7

def test_budget_shortfall():
    res = dfs.predict_lineup(PLAYERS, budget=40)
    assert res["cost"] <= 40
    assert res["remaining_budget"] >= 0
    assert res["complete"] is False
    assert len(res["lineup"]) < 7
