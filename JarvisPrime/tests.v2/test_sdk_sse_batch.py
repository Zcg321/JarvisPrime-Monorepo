import sys, pathlib, json, io
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import sdk.python.jarvisprime.client as client_mod
from sdk.python.jarvisprime.client import JarvisPrime


class DummyResp(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def __iter__(self):
        return iter(self.readlines())


def test_stream_and_batch(monkeypatch):
    def fake_urlopen(req, timeout=None):
        if getattr(req, "full_url", "").endswith("/alerts/stream"):
            data = b"data: {\"alert\":1}\n\n"
            return DummyResp(data)
        return DummyResp(b"{\"ok\":true}")

    monkeypatch.setattr(client_mod.request, "urlopen", fake_urlopen)
    cli = JarvisPrime(token="t", base_url="http://x")
    evt = next(cli.stream_alerts(max_seconds=0.1))
    assert evt["alert"] == 1
    res = cli.chat_batch([{"message": "m"}])
    assert res[0]["ok"]
