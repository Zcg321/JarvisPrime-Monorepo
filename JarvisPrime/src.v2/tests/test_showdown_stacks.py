from src.tools.dfs_showdown import showdown_lineup


def _players():
    return [
        {"name": "CPT", "proj": 10, "cost": 10000, "team": "A", "ownership_gap":0.1, "corr_util":0.1},
        {"name": "A1", "proj": 8, "cost": 8000, "team": "A"},
        {"name": "A2", "proj": 7, "cost": 7000, "team": "A"},
        {"name": "B1", "proj": 6, "cost": 6000, "team": "B"},
        {"name": "B2", "proj": 5, "cost": 5000, "team": "B"},
        {"name": "B3", "proj": 4, "cost": 4000, "team": "B"},
    ]


def test_captain_team_stack():
    res = showdown_lineup(_players(), stacks={"captain_team": True}, seed=0)
    teams = {p["team"] for p in res["lineup"] if p["slot"] != "CPT"}
    assert teams == {"A"}


def test_bringback_stack():
    res = showdown_lineup(_players(), stacks={"captain_team": True, "bringback": True}, seed=0)
    teams = [p["team"] for p in res["lineup"]]
    assert "B" in teams
