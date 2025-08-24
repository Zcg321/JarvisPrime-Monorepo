import json
import os
import subprocess
import time
import urllib.request
import urllib.error


def _call(port, token):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/chat",
        data=json.dumps({"message": "chaos_harness", "args": {}}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        urllib.request.urlopen(req)
        return 200
    except urllib.error.HTTPError as e:
        return e.code


def test_role_policy():
    env = os.environ.copy()
    env["PORT"] = "0"
    proc = subprocess.Popen(
        ["python", "-m", "src.serve.server_stub"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    port = int(proc.stdout.readline().strip())
    time.sleep(0.5)
    assert _call(port, "USER_TOKEN") == 403
    assert _call(port, "ADMIN_TOKEN") == 200
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
