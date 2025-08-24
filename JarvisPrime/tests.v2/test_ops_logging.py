import json
import urllib.request
import urllib.error
import time
import threading
import importlib
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


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


def test_health_and_logs():
    open("logs/server.log", "w").close()
    server, thread, port = _start_server()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as resp:
            data = json.load(resp)
        assert "uptime_s" in data and "config_sha" in data and data["tokens_configured"] >= 1
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/chat",
            data=json.dumps({"message": "savepoint", "args": {"event": "t", "payload": {}}}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError:
            pass
        time.sleep(0.1)
        lines = [json.loads(l) for l in open("logs/server.log").read().splitlines() if l.strip()]
        assert lines
        for log in reversed(lines):
            if log.get("msg", "").startswith("POST"):
                assert {"ts", "level", "msg", "component", "port"} <= set(log.keys())
                assert "role" in log and "lineage_id" in log
                break
    finally:
        server.shutdown(); thread.join()
