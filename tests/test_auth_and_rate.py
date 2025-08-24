import json, os, urllib.request, urllib.error, pytest


def _post(port, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat", data=json.dumps(payload).encode(), headers=headers
    )
    return urllib.request.urlopen(req)


def test_auth_required(server):
    port = server
    with pytest.raises(urllib.error.HTTPError) as e:
        _post(port, {"message": "list_tools"})
    assert e.value.code==401
    r=_post(port,{"message":"list_tools"},token="TEST_TOKEN")
    assert r.getcode()==200

def test_rate_limit(server):
    port = server
    token="TEST_TOKEN"
    for i in range(120):
        try:
            _post(port,{"message":"list_tools"},token=token)
        except urllib.error.HTTPError as exc:
            if exc.code==429:
                break
    else:
        pytest.fail("rate limit not triggered")
