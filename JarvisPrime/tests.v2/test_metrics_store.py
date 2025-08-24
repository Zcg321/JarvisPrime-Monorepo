import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import importlib
import threading
import time
import urllib.request
import urllib.error


def setup_module(module):
    module.tmpdir = tempfile.TemporaryDirectory()
    global tmpdir
    tmpdir = module.tmpdir
    os.environ['METRICS_DIR'] = module.tmpdir.name
    import src.serve.metrics_store as ms
    importlib.reload(ms)
    module.ms = ms


def teardown_module(module):
    module.tmpdir.cleanup()


def _start_server():
    import src.serve.server_stub as stub
    importlib.reload(stub)
    server = stub.HTTPServer(("127.0.0.1", 0), stub.H)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    for _ in range(30):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.2)
            break
        except Exception:
            time.sleep(0.1)
    else:
        server.shutdown(); thread.join(); raise RuntimeError("server did not start")
    return server, thread, port


def test_rollup_and_endpoints():
    t0 = datetime(2025, 1, 1, 0, 10, tzinfo=timezone.utc).timestamp()
    t1 = datetime(2025, 1, 1, 0, 20, tzinfo=timezone.utc).timestamp()
    t2 = datetime(2025, 1, 1, 1, 5, tzinfo=timezone.utc).timestamp()
    ms.log_request(t0, "foo", "fp16", 100.0, "ok")
    ms.log_request(t1, "foo", "fp16", 200.0, "error", "invalid_args")
    ms.log_request(t2, "foo", "fp16", 150.0, "error", "bad")
    roll = Path(tmpdir.name) / "rollup_hourly.jsonl"
    lines = [json.loads(l) for l in roll.read_text().splitlines() if l.strip()]
    assert lines and lines[0]['hour'] == '2025-01-01T00:00:00Z'
    assert lines[0]['count'] == 2
    assert lines[0]['error_count'] == 1
    assert lines[0]['p95_ms'] == 100.0
    server, thread, port = _start_server()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/metrics/rollup/latest",
            headers={"Authorization": "Bearer TEST_TOKEN"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            assert data and data[0]['count'] == 2
        err_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/chat",
            data=json.dumps({"message": "dfs_portfolio", "args": {}}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer USER_TOKEN"},
        )
        try:
            urllib.request.urlopen(err_req, timeout=5)
        except urllib.error.HTTPError:
            pass
    finally:
        server.shutdown(); thread.join()
    req_log = Path(tmpdir.name) / "requests.jsonl"
    last = json.loads(req_log.read_text().splitlines()[-1])
    assert last["status"] == "error" and last["reason"]
