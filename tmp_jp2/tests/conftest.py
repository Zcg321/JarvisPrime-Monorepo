import os
import socket
import subprocess
import time
import urllib.request

import pytest


@pytest.fixture(scope="module")
def server():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    env = os.environ.copy()
    env["PORT"] = str(port)
    proc = subprocess.Popen(["python", "-m", "src.serve.server_stub"], env=env)
    for _ in range(20):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.2):
                break
        except Exception:
            time.sleep(0.1)
    else:
        proc.terminate()
        raise RuntimeError("server did not start")
    yield port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

