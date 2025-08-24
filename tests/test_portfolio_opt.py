from src.tools.dfs_portfolio_opt import optimize


def test_roi_weight_increases_selection():
    lineups = [
        {"id": 1, "roi": 0.1},
        {"id": 2, "roi": 0.3},
        {"id": 3, "roi": -0.2},
    ]
    base = optimize(lineups, {"roi_gain": 0})
    weighted = optimize(lineups, {"roi_gain": 5})
    assert base[0]["id"] == 1
    assert weighted[0]["id"] == 2


def test_deterministic_with_seed():
    lineups = [{"id": i, "roi": i * 0.01} for i in range(5)]
    first = optimize(lineups, {"roi_gain": 1}, seed=42)
    second = optimize(lineups, {"roi_gain": 1}, seed=42)
    assert first == second
