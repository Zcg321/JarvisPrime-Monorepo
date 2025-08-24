from src.serve.server_stub import router
from src.train import uptake

def test_recall_tool(tmp_path):
    uptake.LOG_DIR = tmp_path
    uptake.record({"foo": 1})
    result = router({"tool": "recall", "args": {"n": 1}})
    assert result["experiences"][0]["foo"] == 1
