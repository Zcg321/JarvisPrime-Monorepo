import json
import urllib.request
import pytest
from src.serve import alerts


def test_alerts_stream(server):
    alerts.log_event("policy", "demo")
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/alerts/stream",
        headers={"Authorization": "Bearer ADMIN_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=2) as resp:
        line = resp.readline().decode().strip()
        assert line.startswith("data:")
        data = json.loads(line[5:])
        assert data["type"] == "policy"


def test_alerts_stream_forbidden(server):
    req = urllib.request.Request(f"http://127.0.0.1:{server}/alerts/stream")
    with pytest.raises(Exception):
        urllib.request.urlopen(req, timeout=1)
