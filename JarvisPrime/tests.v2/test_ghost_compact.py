import sys, pathlib, json, importlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


def test_ghost_compact_creates_snapshot(tmp_path, monkeypatch):
    root = tmp_path / "logs" / "ghosts"
    monkeypatch.setenv("ROI_LOG_DIR_TOKENIZED", str(root))
    import src.tools.ghost as ghost
    import scripts.ghost_compact as ghost_compact
    importlib.reload(ghost)
    importlib.reload(ghost_compact)
    token_dir = root / "user1"
    token_dir.mkdir(parents=True)
    (token_dir / "pool.jsonl").write_text("{}\n")
    snap = ghost_compact.compact("user1")
    assert snap.exists()
    manifest = json.loads((snap.parent / "MANIFEST.json").read_text())
    assert manifest["files"][0]["file"] == "pool.jsonl"
    from src.serve.metrics import METRICS
    assert METRICS.ghost_compact_runs >= 1
    assert METRICS.ghost_compact_bytes_reclaimed > 0
