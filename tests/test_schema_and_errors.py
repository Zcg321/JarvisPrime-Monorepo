import json, urllib.request, urllib.error, pytest


def _post(port, data, headers=None):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(data).encode(),
        headers=headers or {"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.getcode(), json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def test_invalid_request(server):
    code,res=_post(server,{"message":5})
    assert code==400 and res["error"]=="BadRequest" and res.get("reason")

def test_unknown_message(server):
    code,res=_post(server,{"message":"nope","args":{}})
    assert code==404 and res["error"]=="unknown_message"

def test_wrong_content_type(server):
    req=urllib.request.Request(f"http://127.0.0.1:{server}/chat",data=b'{}',headers={"Authorization": "Bearer TEST_TOKEN"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code==415
