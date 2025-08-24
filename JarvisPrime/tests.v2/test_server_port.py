import json
import os
import subprocess
import time
from urllib.request import urlopen


def test_server_port():
    env = os.environ.copy()
    env["PORT"] = "0"
    proc = subprocess.Popen(
        ["python", "-m", "src.serve.server_stub"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    port_line = proc.stdout.readline().strip()
    port = int(port_line)
    time.sleep(0.5)
    with urlopen(f"http://127.0.0.1:{port}/health") as resp:
        data = json.load(resp)
    assert data["port"] == port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
