import json
import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import ghost_dfs


def test_seed_deterministic(monkeypatch, tmp_path):
    monkeypatch.setattr(ghost_dfs, "DATA_DIR", tmp_path)
    p1 = ghost_dfs.seed_pool("SLATE", 42, pool_size=5)
    p2 = ghost_dfs.seed_pool("SLATE", 42, pool_size=5)
    assert p1 == p2


def test_mutate_and_roi(monkeypatch, tmp_path):
    monkeypatch.setattr(ghost_dfs, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ghost_dfs, "ROI_LOG", tmp_path / "roi.jsonl")
    pool = ghost_dfs.seed_pool("SLATE", 1, pool_size=2)
    mutated = ghost_dfs.mutate_pool("SLATE", 1, cap=50000)
    assert len(mutated) == len(pool)
    for lu in mutated:
        assert lu["salary_total"] <= 50000
        assert lu["leftover"] == 50000 - lu["salary_total"]
        assert len(lu["players"]) == len(ghost_dfs.ROSTER_CLASSIC)
    ghost_dfs.roi_log("SLATE", "L0", 3, 10.0)
    text = (tmp_path / "roi.jsonl").read_text().strip()
    assert json.loads(text)["lineup_id"] == "L0"
