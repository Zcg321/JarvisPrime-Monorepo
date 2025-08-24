import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import portfolio_diversity


def test_portfolio_diversity_deterministic():
    lineups = [
        {
            "id": "A",
            "players": [{"player_id": "p1"}, {"player_id": "p2"}],
            "roi": 0.1,
            "leverage": 0.2,
        },
        {
            "id": "B",
            "players": [{"player_id": "p1"}, {"player_id": "p3"}],
            "roi": 0.05,
            "leverage": 0.1,
        },
        {
            "id": "C",
            "players": [{"player_id": "p4"}, {"player_id": "p5"}],
            "roi": 0.02,
            "leverage": 0.05,
        },
    ]
    res1 = portfolio_diversity.portfolio_diversity(lineups, {"roi": 1, "leverage": 1, "diversity": 1}, seed=1)
    res2 = portfolio_diversity.portfolio_diversity(lineups, {"roi": 1, "leverage": 1, "diversity": 1}, seed=1)
    assert res1 == res2
    assert res1["selected"] == ["A", "C", "B"]
    assert res1["summary"]["jaccard"] >= 0
