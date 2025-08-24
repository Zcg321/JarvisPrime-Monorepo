import json
import urllib.request
import urllib.error
import pytest


def test_policy_wildcard(server):
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/chat",
        data=json.dumps({"message": "dfs_portfolio"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer USER_TOKEN"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 403
    data = json.loads(exc.value.read().decode())
    assert data.get("error") == "Forbidden"

