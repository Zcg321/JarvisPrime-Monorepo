import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import ghost
import pytest


def test_dfs_sim_deterministic():
    lineup = [{"proj": 10}, {"proj": 5}]
    res = ghost.dfs_sim(lineup, sims=1000, seed=0)
    assert res["mean"] == pytest.approx(15, abs=0.5)
    assert res["p95"] > res["mean"]
