import json
from types import SimpleNamespace
import urllib.request

from sdk.python.jarvisprime.client import JarvisPrime


def test_sdk_client(monkeypatch):
    class Dummy:
        def __init__(self, data):
            self.data = data

        def read(self):
            return self.data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=None):
        url = req if isinstance(req, str) else req.full_url
        if url.endswith("/health"):
            return Dummy(b'{"status":"ok"}')
        return Dummy(b'{"ok": true}')

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with JarvisPrime("T") as c:
        assert c.health()["status"] == "ok"
        assert c.chat("tool") == {"ok": True}
