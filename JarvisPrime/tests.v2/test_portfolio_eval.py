from pathlib import Path
from src.tools.portfolio_eval import evaluate


def test_portfolio_eval(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("logs/savepoints").mkdir(parents=True)
    csv_path = tmp_path / "own.csv"
    csv_path.write_text("player_id,team,proj_points,field_own_pct\nP,TM,10,0.1\n")
    res1 = evaluate([], str(csv_path), iters=100, seed=1)
    res2 = evaluate([], str(csv_path), iters=100, seed=1)
    assert res1 == res2
    assert "ev" in res1
