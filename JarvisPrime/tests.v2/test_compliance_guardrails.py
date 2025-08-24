import json
import subprocess, sys
from pathlib import Path


def test_retention_and_confirm(tmp_path, monkeypatch):
    root = Path(tmp_path)
    monkeypatch.chdir(root)
    audit_dir = root / 'logs/audit'
    sp_dir = root / 'logs/savepoints'
    audit_dir.mkdir(parents=True)
    sp_dir.mkdir(parents=True)
    audit_file = audit_dir / 'a.jsonl'
    audit_file.write_text(
        json.dumps({"ts_iso": "2000-01-01T00:00:00Z", "token_id": "u"}) + "\n" +
        json.dumps({"ts_iso": "2099-01-01T00:00:00Z", "token_id": "u"}) + "\n"
    )
    sp_old = sp_dir / 'old.json'
    sp_old.write_text(json.dumps({"ts_iso": "2000-01-01T00:00:00Z"}))
    sp_new = sp_dir / 'new.json'
    sp_new.write_text(json.dumps({"ts_iso": "2099-01-01T00:00:00Z"}))
    script = Path(__file__).resolve().parents[1] / 'scripts/compliance.py'
    subprocess.check_call([sys.executable, str(script), 'purge', '--retention-days', '30'], cwd=root)
    lines = [json.loads(l) for l in audit_file.read_text().splitlines()]
    assert any(l.get('tombstone') for l in lines)
    out = subprocess.run([sys.executable, str(script), 'purge', '--retention-days', '30', '--simulate'], cwd=root)
    assert out.returncode != 0
    out2 = subprocess.run([sys.executable, str(script), 'purge', '--retention-days', '30', '--simulate', '--confirm'], cwd=root)
    assert out2.returncode == 0
