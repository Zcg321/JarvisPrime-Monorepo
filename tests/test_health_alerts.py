import json
import urllib.request

ADMIN = {"Authorization": "Bearer ADMIN_TOKEN"}
USER = {"Authorization": "Bearer USER_TOKEN"}


def test_health_alert_breakdown(server):
    port = server
    # Trigger a policy alert
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps({"message": "dfs_portfolio", "args": {}}).encode(),
        headers={"Content-Type": "application/json", **USER},
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        pass
    data = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/health").read())
    assert "alerts_by_severity" in data
    assert set(data["alerts_by_severity"].keys()) == {"INFO", "WARN", "ERROR"}
