import json
import hashlib
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

from . import audit


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def export_audit(token_id: str, since: str, until: str, out_path: Path) -> Tuple[Path, Dict[str, Any]]:
    since_dt = datetime.fromisoformat(since.replace('Z','+00:00')) if since else None
    until_dt = datetime.fromisoformat(until.replace('Z','+00:00')) if until else None
    lines = []
    for path in sorted(Path('logs/audit').glob('*.jsonl')):
        with path.open() as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if token_id and rec.get('token_id') != token_id:
                    continue
                ts = rec.get('ts_iso')
                if ts:
                    ts_dt = datetime.fromisoformat(ts.replace('Z','+00:00'))
                    if since_dt and ts_dt < since_dt:
                        continue
                    if until_dt and ts_dt > until_dt:
                        continue
                lines.append(audit._redact(rec))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        audit_file = tmpdir / 'audit.jsonl'
        with audit_file.open('w', encoding='utf-8') as f:
            for rec in lines:
                f.write(json.dumps(rec) + '\n')
        manifest = {
            'audit.jsonl': {
                'count': len(lines),
                'sha256': _sha256(audit_file),
            }
        }
        manifest_file = tmpdir / 'MANIFEST.json'
        manifest_file.write_text(json.dumps(manifest))
        with tarfile.open(out_path, 'w:gz') as tar:
            tar.add(audit_file, arcname='audit.jsonl')
            tar.add(manifest_file, arcname='MANIFEST.json')
    return out_path, manifest
