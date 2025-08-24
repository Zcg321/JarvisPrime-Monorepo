import urllib.request
import urllib.request


def test_prom_metrics(server):
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/metrics/prom",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        text = resp.read().decode()
    assert "requests_total" in text and "latency_p95" in text
