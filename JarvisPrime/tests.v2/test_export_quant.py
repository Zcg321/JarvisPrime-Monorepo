import json
import subprocess
from pathlib import Path

def test_export_quant(tmp_path):
    model = tmp_path / "base"
    model.mkdir()
    out = tmp_path / "quant"
    cmd = ["python", "scripts/export_quant.py", "--model", str(model), "--out", str(out), "--method", "awq"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert (out / "model_index.json").exists()
    assert (out / "adapter").is_dir()
    assert (out / "weights").is_dir()
    notes = (out / "notes.txt").read_text()
    assert "method=" in notes
    assert proc.returncode == 0
