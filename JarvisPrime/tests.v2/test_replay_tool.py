from src.serve.server_stub import router
from src.train import uptake

def test_replay_tool(tmp_path):
    uptake.LOG_DIR = tmp_path
    uptake.record({"v": 1})
    uptake.record({"v": 2})
    result = router({"tool": "replay", "args": {}})
    assert [e["v"] for e in result["experiences"]] == [1, 2]
