import json
import subprocess
from pathlib import Path


def test_lineage_viz(tmp_path):
    sp = tmp_path / "logs/savepoints"
    sp.mkdir(parents=True)
    (sp / "a.json").write_text(json.dumps({"event": "dfs", "lineage_id": "A", "ts_iso": "2025", "payload": {}, "sha256_payload": "x"}))
    (sp / "b.json").write_text(json.dumps({"event": "dfs", "lineage_id": "B", "parent_id": "A", "ts_iso": "2025", "payload": {}, "sha256_payload": "x"}))
    script = Path(__file__).resolve().parents[1] / "scripts/lineage_viz.py"
    subprocess.run(["python", str(script)], cwd=tmp_path, check=True)
    dot = (tmp_path / "artifacts/reports/lineage.dot").read_text()
    assert '"A" -> "B"' in dot
    html = (tmp_path / "artifacts/reports/lineage.html").read_text()
    assert "digraph" in html
