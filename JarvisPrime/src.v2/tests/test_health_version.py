import json, urllib.request


def test_health(server):
    with urllib.request.urlopen(f"http://127.0.0.1:{server}/health") as r:
        data=json.loads(r.read().decode())
    assert data["status"]=="ok" and "uptime_s" in data

def test_version(server):
    with urllib.request.urlopen(f"http://127.0.0.1:{server}/version") as r:
        data=json.loads(r.read().decode())
    assert data["version"]=="nova-prime-v2" and data["tools_count"]>0
