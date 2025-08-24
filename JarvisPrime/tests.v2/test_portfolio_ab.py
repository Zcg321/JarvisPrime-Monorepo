import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import portfolio_ab


def test_portfolio_ab_deterministic(tmp_path):
    own = tmp_path / "own.csv"
    own.write_text("player,own\n")
    A = {"lineups": [[1, 1], [2, 2]]}
    B = {"lineups": [[3, 3], [4, 4]]}
    res1 = portfolio_ab.portfolio_ab(A, B, str(own), iters=100, seed=1)
    res2 = portfolio_ab.portfolio_ab(A, B, str(own), iters=100, seed=1)
    assert res1 == res2
    assert abs(res1["lift_ev"]) > 0
