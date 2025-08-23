from fastapi.testclient import TestClient
from jarvis_plugins.app import build_app
from pathlib import Path
import os, json


def test_rag_rebuild_endpoint(tmp_path, monkeypatch):
    # isolate rag dir
    monkeypatch.setenv("JARVIS_RAG_DIR", str(tmp_path / "rag"))
    c = TestClient(build_app())
    r = c.post("/plugins/rag/rebuild")
    assert r.status_code == 200
    out = r.json()
    assert out["ok"] is True
    jidx = Path(out["index_dir"]) / "index.json"
    assert jidx.exists()


def test_autosync_on_savepoint(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_RAG_DIR", str(tmp_path / "rag2"))
    monkeypatch.setenv("JARVIS_DNA_AUTOSYNC", "1")
    from jarvis_plugins.savepoint import SavepointLogger
    sp = SavepointLogger(base_dir=str(tmp_path / "sps"))
    sp.create({"note":"hello rag"}, tag="unit")
    from jarvis_plugins import dna_sync
    jidx = dna_sync.JSON_INDEX
    # autosync appends JSON entry
    assert jidx.exists()
    data = json.loads(jidx.read_text())
    assert len(data.get("entries", [])) >= 1
