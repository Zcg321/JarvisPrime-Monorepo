import json
import subprocess
import sys
from pathlib import Path


def test_e2e_smoke(tmp_path):
    out = subprocess.check_output([sys.executable, "scripts/e2e_smoke.py"])
    data = json.loads(out)
    assert "slates" in data and "ev" in data
    assert any(Path("logs/savepoints").glob("*.json"))
