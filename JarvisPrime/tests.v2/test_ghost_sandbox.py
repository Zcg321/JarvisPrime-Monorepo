import json
from pathlib import Path

from src.tools import ghost_dfs
from src.reflex import policy as risk_policy
import os
import importlib
from src.tools import ghost as ghost_mod


def test_token_scoped_ghost(tmp_path, monkeypatch):
    monkeypatch.setenv("ROI_LOG_DIR_TOKENIZED", str(tmp_path))
    monkeypatch.setenv("ROI_LOG_DIR_LEGACY", str(tmp_path / "legacy"))
    monkeypatch.setenv("ROI_LOG_COMPAT_MIRROR", "1")
    importlib.reload(ghost_mod)
    globals()["ghost_dfs"] = importlib.reload(ghost_dfs)
    slate = "TEST_SLATE"
    seed = 42
    risk_policy.set_token("userA")
    pool_a = ghost_dfs.seed_pool(slate, seed, pool_size=2, token_id="userA")
    path_a = tmp_path / "userA" / f"{slate}_{seed}_seed.json"
    assert path_a.exists()

    risk_policy.set_token("userB")
    pool_b = ghost_dfs.seed_pool(slate, seed, pool_size=2, token_id="userB")
    path_b = tmp_path / "userB" / f"{slate}_{seed}_seed.json"
    assert path_b.exists()
    assert path_a.read_text() != path_b.read_text()

    # fallback to legacy read
    legacy_file = (tmp_path / "legacy" / f"{slate}_{seed}_seed.json")
    legacy_file.parent.mkdir(parents=True, exist_ok=True)
    legacy_file.write_text(path_a.read_text())
    risk_policy.set_token("userC")
    pool_c = ghost_dfs.mutate_pool(slate, seed, token_id="userC")
    assert pool_c == json.loads(legacy_file.read_text())

    # ROI log mirrors to legacy
    ghost_dfs.roi_log(slate, "L0", 1, 1.0, token_id="userA")
    assert (tmp_path / "userA" / "roi.jsonl").exists()
    assert (tmp_path / "legacy" / "roi.jsonl").exists()
