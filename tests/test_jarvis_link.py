from fastapi.testclient import TestClient
import httpx
from jarvis_plugins.app import build_app


def test_link_openai(monkeypatch):
    # prepare environment variables
    monkeypatch.setenv("OPENAI_API_URL", "https://example.com/ai")
    monkeypatch.setenv("OPENAI_API_KEY", "secret")
    called = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        called["url"] = url
        called["json"] = json
        called["headers"] = headers
        req = httpx.Request("POST", url)
        return httpx.Response(200, json={"echo": json["prompt"]}, request=req)

    monkeypatch.setattr(httpx, "post", fake_post)
    c = TestClient(build_app())
    r = c.post("/plugins/link", json={"target": "openai", "prompt": "hi"})
    assert r.status_code == 200
    assert r.json()["echo"] == "hi"
    assert called["url"] == "https://example.com/ai"
    assert called["headers"]["Authorization"] == "Bearer secret"
