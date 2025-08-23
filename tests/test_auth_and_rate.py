import json, os, subprocess, time, urllib.request, urllib.error
import pytest

@pytest.fixture
def server():
    env=os.environ.copy(); env["AUTH_TOKEN"]="secret"
    proc = subprocess.Popen(["python","-m","src.serve.server_stub"],env=env)
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/health",timeout=0.2)
            break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate(); raise RuntimeError("server did not start")
    yield
    proc.terminate(); proc.wait(timeout=5)

def _post(payload, token=None):
    headers={"Content-Type":"application/json"}
    if token: headers["X-Auth-Token"]=token
    req=urllib.request.Request("http://127.0.0.1:8000/chat",data=json.dumps(payload).encode(),headers=headers)
    return urllib.request.urlopen(req)

def test_auth_required(server):
    with pytest.raises(urllib.error.HTTPError) as e:
        _post({"message":"list_tools"})
    assert e.value.code==401
    r=_post({"message":"list_tools"},token="secret")
    assert r.getcode()==200

def test_rate_limit(server):
    token="secret"
    for i in range(20):
        _post({"message":"list_tools"},token=token)
    with pytest.raises(urllib.error.HTTPError) as e:
        _post({"message":"list_tools"},token=token)
    assert e.value.code==429
