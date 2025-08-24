from src.serve.server_stub import router
from src.tools import savepoint

def test_savepoint_list(tmp_path, monkeypatch):
    monkeypatch.setattr(savepoint, "SAVE_DIR", tmp_path)
    savepoint.save("moment one", {"x": 1})
    result = router({"tool": "savepoint_list", "args": {"n": 1}})
    sp = result["savepoints"][0]
    assert sp["moment"] == "moment one"
    assert sp["meta"] == {"x": 1}
    assert "ts" in sp
