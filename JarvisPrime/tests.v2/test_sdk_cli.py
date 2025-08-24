import json
import pathlib
import sys
import urllib.error

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "sdk/python"))

from jarvisprime import client as jp
from cli import jarvisctl


def test_client_retries(monkeypatch):
    attempts = {"n": 0}

    class Resp:
        def read(self):
            return b"{\"ok\": true}"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise urllib.error.HTTPError(req.full_url, 500, "err", {}, None)
        return Resp()

    monkeypatch.setattr(jp.request, "urlopen", urlopen)
    monkeypatch.setattr(jp.time, "sleep", lambda s: None)
    c = jp.JarvisPrime("tok", "http://x")
    assert c.health() == {"ok": True}
    assert attempts["n"] == 3


def test_jarvisctl_parsing(monkeypatch, capsys):
    called = {}

    class Dummy(jp.JarvisPrime):
        def health(self):
            called["health"] = True
            return {"ok": True}

    monkeypatch.setattr(jarvisctl, "JarvisPrime", Dummy)
    jarvisctl.main(["health"])
    assert called["health"]
