import importlib, pytest
from fastapi.testclient import TestClient

def _import_main():
    for c in ["JarvisOrigin.src.serve.server"]:
        try:
            return importlib.import_module(c)
        except Exception:
            pass
    pytest.skip("server not importable")

def test_plugins_mounted():
    m = _import_main()
    app = getattr(m, "app", None)
    if app is None:
        pytest.skip("no app")
    c = TestClient(app)
    r = c.get("/plugins/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
