import json, urllib.request
from pathlib import Path
from src.tools import dfs_roi_memory


def _post(port, payload):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def test_calibration_monotone(server):
    port = server
    dfs_roi_memory.record_result(["A"],10,10)
    dfs_roi_memory.record_result(["A"],10,20)
    players=[{"name":"A","proj":10},{"name":"B","proj":10}]
    res=_post(port,{"message":"dfs_calibrate","args":{"players":players,"seed":1}})
    pa=[p for p in res["players"] if p["name"]=="A"][0]
    pb=[p for p in res["players"] if p["name"]=="B"][0]
    assert pa["proj"]>pb["proj"]
