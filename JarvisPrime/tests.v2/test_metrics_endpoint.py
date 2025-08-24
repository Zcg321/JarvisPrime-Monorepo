import sys
import pathlib
import json
import urllib.request

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))


def test_metrics_endpoint(server):
    payload = b'{"message":"dfs","args":{"players":[],"budget":0}}'
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/chat", data=payload,
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"}
    )
    urllib.request.urlopen(req).read()
    data = json.loads(
        urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{server}/metrics",
                headers={"Authorization": "Bearer TEST_TOKEN"},
            )
        ).read().decode()
    )
    assert data["requests_total"] >= 1
    assert data["dfs_builds"] >= 1
