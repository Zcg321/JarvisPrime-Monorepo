import json
import subprocess, sys
from pathlib import Path

def test_compliance_attestation(tmp_path, monkeypatch):
    root = Path(tmp_path)
    monkeypatch.chdir(root)
    (root / 'logs/audit').mkdir(parents=True)
    rec = {"ts_iso": "2000-01-01T00:00:00Z", "token_id": "user1"}
    (root / 'logs/audit/a.jsonl').write_text(json.dumps(rec) + '\n')
    script = Path(__file__).resolve().parents[1] / 'scripts/compliance.py'
    subprocess.check_call([sys.executable, str(script), 'purge', '--token-id', 'user1', '--simulate', '--confirm'], cwd=root)
    att_dir = root / 'logs/compliance/attestations'
    files = list(att_dir.glob('receipt_*.json'))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    expected_hash = __import__('hashlib').sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    assert data['hash'] == expected_hash
