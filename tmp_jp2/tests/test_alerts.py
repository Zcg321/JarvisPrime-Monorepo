import json
import urllib.request

ADMIN = {"Authorization": "Bearer ADMIN_TOKEN"}
USER = {"Authorization": "Bearer USER_TOKEN"}


def test_alerts_logged_and_endpoint(server):
    port = server
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps({"message": "dfs_portfolio", "args": {}}).encode(),
        headers={"Content-Type": "application/json", **USER},
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        pass
    req2 = urllib.request.Request(f"http://127.0.0.1:{port}/alerts?page=1&page_size=100", headers=ADMIN)
    data = json.loads(urllib.request.urlopen(req2).read())
    assert any(rec.get("type") == "policy_deny" for rec in data["items"])
    req3 = urllib.request.Request(f"http://127.0.0.1:{port}/alerts", headers=USER)
    try:
        urllib.request.urlopen(req3)
        raise AssertionError("non-admin allowed")
    except urllib.error.HTTPError as e:
        assert e.code == 403
    req4 = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps({"message": "lineup_agent", "args": {"seed_lineup": {"players": []}}}).encode(),
        headers={"Content-Type": "application/json", **USER},
    )
    try:
        urllib.request.urlopen(req4)
    except urllib.error.HTTPError:
        pass
    snap = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{port}/metrics", headers=ADMIN)
        ).read()
    )
    assert snap.get("forbidden_total", {}).get("role policy")
