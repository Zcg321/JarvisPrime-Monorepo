from src.tools.slate_sim import run


def test_slate_sim_deterministic(tmp_path):
    lineups = [["A","B"],["C"]]
    csv = "data/ownership/sample_classic.csv"
    r1 = run(lineups, csv, iters=100, seed=1)
    r2 = run(lineups, csv, iters=100, seed=1)
    assert r1 == r2
    assert "roi_distribution" in r1
