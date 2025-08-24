from pathlib import Path
from JarvisOrigin.src.export import int8_export

def test_export_guard_runs_without_torch(monkeypatch):
    monkeypatch.setattr(int8_export, "HAS_TORCH", False)
    out = int8_export.dynamic_int8_export(None, "artifacts/export/test_guard")
    meta = Path(out)/"export_meta.json"
    assert meta.exists()
    j = meta.read_text()
    assert "torch not installed" in j
