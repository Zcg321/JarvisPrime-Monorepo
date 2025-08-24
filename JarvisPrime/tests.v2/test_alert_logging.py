import json
import urllib.request
from pathlib import Path

USER = {"Authorization": "Bearer USER_TOKEN"}


def test_alert_log_line(server):
    port = server
    log_path = Path("logs/server.log")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps({"message": "dfs_portfolio", "args": {}}).encode(),
        headers={"Content-Type": "application/json", **USER},
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        pass
    lines = [json.loads(l) for l in log_path.read_text().splitlines()]
    assert any(l.get("level") == "ALERT" for l in lines)
