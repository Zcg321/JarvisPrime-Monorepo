import json
import os
import urllib.request
import threading
import time
import importlib
from pathlib import Path


def setup_module(module):
    logs = Path('logs')
    logs.mkdir(exist_ok=True)
    (logs/ 'alerts.jsonl').write_text('{}\n')
    audit = logs/'audit'
    audit.mkdir(exist_ok=True)
    (audit/'audit.jsonl').write_text('{}\n')
    metrics = logs/'metrics'
    metrics.mkdir(parents=True, exist_ok=True)
    (metrics/'requests.jsonl').write_text('{}\n')


def _start_server():
    import src.serve.server_stub as stub
    importlib.reload(stub)
    server = stub.HTTPServer(('127.0.0.1',0), stub.H)
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


def test_status_and_rebuild(tmp_path):
    from src.serve import indexer
    stat = indexer.status()
    assert stat['audit']['rows'] == 1
    # corrupt file
    Path('logs/audit/audit.jsonl').write_text('bad\n')
    stat2 = indexer.status()
    assert stat2['audit']['rebuilt'] >= 1
    server, thread, port = _start_server()
    try:
        req = urllib.request.Request(
            f'http://127.0.0.1:{port}/indexes/status',
            headers={'Authorization':'Bearer ADMIN_TOKEN'}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            assert 'audit' in data
        req2 = urllib.request.Request(
            f'http://127.0.0.1:{port}/indexes/rebuild',
            data=json.dumps({'which':'all'}).encode(),
            headers={'Content-Type':'application/json','Authorization':'Bearer ADMIN_TOKEN'}
        )
        with urllib.request.urlopen(req2, timeout=5) as resp:
            data2 = json.loads(resp.read().decode())
            assert 'audit' in data2
    finally:
        server.shutdown(); thread.join()
