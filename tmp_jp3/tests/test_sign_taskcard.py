import os
import subprocess
import sys
import hmac
import hashlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sign_taskcard.py"


def _run(body: str, token: str) -> str:
    env = os.environ.copy()
    env["FOREMAN_SHARED_TOKEN"] = token
    out = subprocess.check_output([sys.executable, str(SCRIPT), body], env=env)
    return out.decode().strip()


def _hmac(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def test_sign(monkeypatch):
    body = '{"task_card":"Add LICENSE"}'
    token = "tok"
    assert _run(body, token) == _hmac(body, token)


def test_sign_trailing_newline(monkeypatch):
    body = '{"task_card":"Add LICENSE"}\n'
    token = "tok"
    assert _run(body, token) == _hmac(body, token)
