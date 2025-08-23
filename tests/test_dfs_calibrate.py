import json, subprocess, time, urllib.request
import pytest
from pathlib import Path
from src.tools import dfs_roi_memory

@pytest.fixture(scope="module")
def server():
    dfs_roi_memory.LOG_PATH = Path("logs/dfs_roi.jsonl")
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
    if dfs_roi_memory.LOG_PATH.exists():
        dfs_roi_memory.LOG_PATH.unlink()

def _post(payload):
    req=urllib.request.Request("http://127.0.0.1:8000/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def test_calibration_monotone(server):
    dfs_roi_memory.record_result(["A"],10,10)
    dfs_roi_memory.record_result(["A"],10,20)
    players=[{"name":"A","proj":10},{"name":"B","proj":10}]
    res=_post({"message":"dfs_calibrate","args":{"players":players,"seed":1}})
    pa=[p for p in res["players"] if p["name"]=="A"][0]
    pb=[p for p in res["players"] if p["name"]=="B"][0]
    assert pa["proj"]>pb["proj"]
