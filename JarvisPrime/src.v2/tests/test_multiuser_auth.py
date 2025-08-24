import json, urllib.request, urllib.error, time, threading, importlib, pathlib, os
import pytest

sys_path_added = False
if True:
    import sys
    if str(pathlib.Path(__file__).resolve().parents[1]) not in sys.path:
        sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


def _write_config():
    cfg = pathlib.Path('configs/server.yaml')
    orig = cfg.read_text()
    cfg.write_text(
        "require_auth: true\n"
        "tokens:\n"
        "  - id: admin\n    token: ADMIN_TOKEN\n    role: admin\n"
        "  - id: user\n    token: USER_TOKEN\n    role: user\n"
        "rate:\n  rps: 100\n  burst: 100\n"
        "policies:\n  - role: user\n    allow: [\"dfs_*\", \"voice_mirror\"]\n    deny: [\"chaos_harness\"]\n"
    )
    return orig


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


def test_multiuser(tmp_path):
    cfg_path = pathlib.Path('configs/server.yaml')
    orig = _write_config()
    audit_file = pathlib.Path('logs/audit/audit.jsonl')
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.write_text("")
    server, thread, port = _start_server()
    try:
        req_admin = urllib.request.Request(
            f"http://127.0.0.1:{port}/chat",
            data=json.dumps({"message": "chaos_harness"}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer ADMIN_TOKEN"},
        )
        with urllib.request.urlopen(req_admin, timeout=5) as resp:
            assert resp.getcode() == 200
        req_user = urllib.request.Request(
            f"http://127.0.0.1:{port}/chat",
            data=json.dumps({"message": "chaos_harness"}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer USER_TOKEN"},
        )
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(req_user, timeout=5)
        assert exc.value.code == 403
        lines = [json.loads(l) for l in audit_file.read_text().splitlines() if l.strip()]
        assert lines and lines[0].get("token_id") == "admin"
    finally:
        server.shutdown(); thread.join()
        cfg_path.write_text(orig)
