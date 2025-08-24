import json
import subprocess
from pathlib import Path


def test_lineage_ui(tmp_path):
    sp = tmp_path / "logs/savepoints"
    sp.mkdir(parents=True)
    (sp / "a.json").write_text(json.dumps({"event": "t1", "lineage_id": "A"}))
    (sp / "b.json").write_text(json.dumps({"event": "t2", "lineage_id": "B", "parent_id": "A"}))
    script = Path(__file__).resolve().parents[1] / "scripts/lineage_ui.py"
    subprocess.run(["python", str(script)], check=True, cwd=tmp_path)
    out = (tmp_path / "artifacts/reports/lineage_ui.html").read_text()
    assert "<script>" in out and "A" in out and "B" in out

