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


NBA_PLAYERS = [
    {"name": "PG1", "pos": "PG", "cost": 9, "proj": 40},
    {"name": "SG1", "pos": "SG", "cost": 8, "proj": 38},
    {"name": "SF1", "pos": "SF", "cost": 7, "proj": 35},
    {"name": "PF1", "pos": "PF", "cost": 6, "proj": 33},
    {"name": "C1", "pos": "C", "cost": 5, "proj": 32},
    {"name": "GFlex", "pos": "PG/SG", "cost": 4, "proj": 31},
    {"name": "FFlex", "pos": "SF/PF", "cost": 5, "proj": 20},
    {"name": "UTIL1", "pos": "C", "cost": 2, "proj": 29},
]


def test_dk_lineup_schema():
    roster = {"PG": 1, "SG": 1, "SF": 1, "PF": 1, "C": 1, "G": 1, "F": 1, "UTIL": 1}
    res = dfs.predict_lineup(NBA_PLAYERS, budget=46, roster=roster)
    assert res["complete"] is True
    assert res["cost"] == 46
    counts = {}
    for p in res["lineup"]:
        counts[p["slot"]] = counts.get(p["slot"], 0) + 1
    assert counts == roster
