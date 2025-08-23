import json, subprocess, time, urllib.request, urllib.error
import pytest

@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(["python", "-m", "src.serve.server_stub"])
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=0.2)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate(); raise RuntimeError("server did not start")
    yield
    proc.terminate(); proc.wait(timeout=5)

def _post(data, headers=None):
    req=urllib.request.Request(
        "http://127.0.0.1:8000/chat",
        data=json.dumps(data).encode(),
        headers=headers or {"Content-Type":"application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return r.getcode(), json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def test_invalid_request(server):
    code,res=_post({"message":5})
    assert code==400 and res["error"]=="invalid_request"

def test_unknown_message(server):
    code,res=_post({"message":"nope","args":{}})
    assert code==404 and res["error"]=="unknown_message"

def test_wrong_content_type(server):
    req=urllib.request.Request("http://127.0.0.1:8000/chat",data=b'{}',headers={})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code==415
