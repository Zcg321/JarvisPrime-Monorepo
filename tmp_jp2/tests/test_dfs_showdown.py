import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import dfs_showdown


def test_showdown_cpt_and_cap():
    players = [
        {"name": "A", "cost": 1000, "proj": 10, "pos": "PG", "ownership_gap": 0.2},
        {"name": "B", "cost": 1000, "proj": 10, "pos": "PG"},
        {"name": "C", "cost": 1000, "proj": 10, "pos": "PG"},
        {"name": "D", "cost": 1000, "proj": 10, "pos": "PG"},
        {"name": "E", "cost": 1000, "proj": 10, "pos": "PG"},
        {"name": "F", "cost": 1000, "proj": 10, "pos": "PG"},
    ]
    lineup1 = dfs_showdown.showdown_lineup(players, 50000)
    lineup2 = dfs_showdown.showdown_lineup(players, 50000)
    assert lineup1 == lineup2
    cpt = lineup1["lineup"][0]
    assert cpt["slot"] == "CPT"
    assert cpt["name"] == "A"
    assert lineup1["cost"] == 1500 + 5 * 1000
    assert lineup1["cost"] <= 50000
    assert lineup1["remaining_budget"] == 50000 - lineup1["cost"]
