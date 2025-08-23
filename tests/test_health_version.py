import json, subprocess, time, urllib.request
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

def test_health(server):
    with urllib.request.urlopen("http://127.0.0.1:8000/health") as r:
        data=json.loads(r.read().decode())
    assert data["status"]=="ok" and "uptime_s" in data

def test_version(server):
    with urllib.request.urlopen("http://127.0.0.1:8000/version") as r:
        data=json.loads(r.read().decode())
    assert data["version"]=="nova-prime-v2" and data["tools_count"]>0
