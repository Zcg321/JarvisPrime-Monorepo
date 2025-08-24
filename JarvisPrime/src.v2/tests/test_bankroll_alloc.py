from pathlib import Path
from src.tools.bankroll_alloc import allocate


def test_bankroll_alloc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("configs").mkdir()
    Path("logs/savepoints").mkdir(parents=True)
    Path("configs/bankroll.yaml").write_text("unit_fraction: 0.02\n")
    res = allocate(
        bankroll=1000.0,
        slates=[{"id": "S1", "type": "classic", "entries": 10, "avg_entry_fee": 5.0, "edge_hint": 0.1}],
        seed=1,
    )
    assert res["allocations"][0]["entries"] <= 10
    assert res["remaining"] >= 0
    assert (Path("logs/savepoints").exists())
