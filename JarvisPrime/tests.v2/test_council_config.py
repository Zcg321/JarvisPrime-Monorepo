import importlib
from pathlib import Path

import pytest


def test_council_overrides(tmp_path, monkeypatch):
    cfg = tmp_path / "council.yaml"
    cfg.write_text("goku:\n  leverage: 0.7\n")
    monkeypatch.setenv("COUNCIL_CONFIG", str(cfg))
    from src.tools import dfs_scoring
    importlib.reload(dfs_scoring)
    assert dfs_scoring.adjust_projection(10.0, 0.5, "goku") == pytest.approx(13.5)
    assert dfs_scoring.adjust_projection(10.0, 0.5, "gohan") == pytest.approx(11.25)
