import json
import urllib.request
from pathlib import Path
from scripts import compliance


def test_compliance_audit_trail(server):
    Path('logs/audit').mkdir(parents=True, exist_ok=True)
    Path('logs/savepoints').mkdir(parents=True, exist_ok=True)
    (Path('logs/audit') / 'a.jsonl').write_text(json.dumps({'ts_iso':'2025-10-25T00:00:00Z'})+'\n')
    compliance.export(token_id=None)
    trail = Path('logs/compliance/audit_trail/audit.jsonl')
    assert trail.exists()
    req = urllib.request.Request(
        f'http://127.0.0.1:{server}/compliance/audit',
        headers={'Authorization':'Bearer ADMIN_TOKEN'}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    assert data and data[-1]['action'] == 'export'
