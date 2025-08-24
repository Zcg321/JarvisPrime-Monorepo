import json
import urllib.request
import urllib.error

import pytest


def _call(port, token, body):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req)


def test_flags_canary(server):
    port = server
    req_reset = urllib.request.Request(
        f"http://127.0.0.1:{port}/flags/flip",
        data=json.dumps({"name": "lineup_agent", "state": "canary", "percent": 0}).encode(),
        headers={"Authorization": "Bearer ADMIN_TOKEN", "Content-Type": "application/json"},
    )
    urllib.request.urlopen(req_reset)
    with pytest.raises(urllib.error.HTTPError) as e:
        _call(port, "USER_TOKEN", {"message": "lineup_agent", "args": {"seed_lineup": {"players": []}}})
    assert e.value.code == 403
    err = json.loads(e.value.read())
    assert err.get("reason") == "not_canary"
    resp = _call(port, "ADMIN_TOKEN", {"message": "lineup_agent", "args": {"seed_lineup": {"players": []}}})
    data = json.loads(resp.read())
    assert "best_lineup" in data
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/flags/flip",
        data=json.dumps({"name": "lineup_agent", "state": "on"}).encode(),
        headers={"Authorization": "Bearer ADMIN_TOKEN", "Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)
    resp2 = _call(port, "USER_TOKEN", {"message": "lineup_agent", "args": {"seed_lineup": {"players": []}}})
    assert "best_lineup" in json.loads(resp2.read())
