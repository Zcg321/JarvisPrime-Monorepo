import json
import urllib.request
from pathlib import Path


def test_audit_query_api(server):
    port = server
    adir = Path("logs/audit")
    adir.mkdir(parents=True, exist_ok=True)
    rec = {"ts_iso": "2025-10-25T00:00:00Z", "tool": "dfs", "token_id": "user1", "result_status": 200}
    (adir / "audit.jsonl").write_text(json.dumps(rec) + "\n")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/audit/query?tool=dfs&format=json&page=1&page_size=100",
        headers={"Authorization": "Bearer ADMIN_TOKEN"},
    )
    data = urllib.request.urlopen(req).read()
    out = json.loads(data.decode())
    assert out["items"] and out["items"][0]["tool"] == "dfs"
    req2 = urllib.request.Request(
        f"http://127.0.0.1:{port}/audit/query?tool=dfs&format=json",
        headers={"Authorization": "Bearer USER_TOKEN"},
    )
    try:
        urllib.request.urlopen(req2)
    except urllib.error.HTTPError as e:
        assert e.code == 403
    else:
        assert False, "expected 403"
