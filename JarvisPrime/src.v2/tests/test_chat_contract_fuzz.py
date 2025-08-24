import json
import subprocess
import time
import urllib.request
import urllib.error
import pytest
import json


def test_fuzz(server):
    cases = [
        b"[]",
        b"\"str\"",
        json.dumps({"message": 1}).encode(),
        json.dumps({"message": "dfs", "args": []}).encode(),
        json.dumps({"message": "dfs", "args": {"budget": 1e309}}).encode(),
        json.dumps({"message": "dfs_portfolio", "args": {"slates": []}}).encode(),
        json.dumps({"message": "dfs_portfolio", "args": {"slates": [{"id": "A", "type": "bad"}], "n_lineups": 1}}).encode(),
        json.dumps({"message": "dfs_portfolio", "args": {"slates": [{"id": "A", "type": "classic"}], "n_lineups": 1, "scoring_mode": "none"}}).encode(),
        b"{\xff}",
    ]
    url = f"http://127.0.0.1:{server}/chat"
    for payload in cases:
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"})
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=5)
        assert e.value.code in (400, 404)
        body = json.loads(e.value.read().decode())
        if e.value.code == 400:
            assert body.get("error") == "BadRequest"
            assert "reason" in body
    kill = json.dumps({"message": "lights out, jarvis"}).encode()
    req = urllib.request.Request(url, data=kill, headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert json.loads(resp.read().decode()) == {"status": "standby"}
    with urllib.request.urlopen(
        urllib.request.Request(f"http://127.0.0.1:{server}/metrics", headers={"Authorization": "Bearer TEST_TOKEN"}), timeout=5
    ) as resp:
        m = json.loads(resp.read().decode())
    assert m.get("errors_total", 0) >= len(cases)
