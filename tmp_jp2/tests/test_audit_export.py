import json
import os
import tarfile
import tempfile
import urllib.request
import threading
import time
import importlib
from pathlib import Path


def setup_module(module):
    audit_dir = Path('logs/audit')
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / 'audit.jsonl'
    rec = {
        'ts_iso': '2025-10-25T12:00:00Z',
        'token_id': 'user1',
        'tool': 'voice_mirror',
        'args': {'token': 'secret'}
    }
    audit_file.write_text(json.dumps(rec) + '\n')


def _start_server():
    import src.serve.server_stub as stub
    importlib.reload(stub)
    server = stub.HTTPServer(('127.0.0.1', 0), stub.H)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=0.2)
            break
        except Exception:
            time.sleep(0.1)
    else:
        server.shutdown(); thread.join(); raise RuntimeError('server did not start')
    return server, thread, port


def test_cli_and_api(tmp_path):
    from src.serve.audit_export import export_audit
    out = tmp_path / 'out.tar.gz'
    export_audit('user1', '2025-10-25T00:00:00Z', '2025-10-26T00:00:00Z', out)
    with tarfile.open(out, 'r:gz') as tar:
        names = tar.getnames()
        assert 'audit.jsonl' in names and 'MANIFEST.json' in names
        audit_data = tar.extractfile('audit.jsonl').read().decode()
        assert '[REDACTED]' in audit_data
    server, thread, port = _start_server()
    try:
        req = urllib.request.Request(
            f'http://127.0.0.1:{port}/audit/export?token_id=user1&since=2025-10-25T00:00:00Z&until=2025-10-26T00:00:00Z',
            headers={'Authorization': 'Bearer ADMIN_TOKEN'},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            assert data['ok'] and 'manifest' in data
    finally:
        server.shutdown(); thread.join()
