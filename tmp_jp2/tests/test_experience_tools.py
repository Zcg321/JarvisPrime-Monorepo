from pathlib import Path
from src.serve.server_stub import router
from src.train import uptake


def test_experience_stats(tmp_path):
    uptake.LOG_DIR = tmp_path
    first = uptake.record({"text": "first"})
    second = uptake.record({"text": "second"})
    result = router({"tool": "experience_stats", "args": {}})
    assert result["count"] == 2
    assert result["last_ts"] == int(Path(second).stem)


def test_experience_search(tmp_path):
    uptake.LOG_DIR = tmp_path
    uptake.record({"text": "alpha"})
    uptake.record({"text": "beta"})
    result = router({"tool": "experience_search", "args": {"query": "alp"}})
    assert len(result["experiences"]) == 1
    assert result["experiences"][0]["text"] == "alpha"
