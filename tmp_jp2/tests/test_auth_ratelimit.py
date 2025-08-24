import urllib.error
import urllib.request
import json
import pytest


def test_auth_and_rate_limit(server):
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/chat",
        data=json.dumps({"message": "list_tools"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 401
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/chat",
        data=json.dumps({"message": "list_tools"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.getcode() == 200
    for _ in range(120):
        try:
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                break
    else:
        pytest.fail("rate limit not triggered")
