import json, pathlib
from src.serve.server_stub import reply
from src.train import uptake

def test_reply_records_experience(tmp_path):
    uptake.LOG_DIR = tmp_path
    reply("hello")
    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text())
    assert data["user"] == "hello"
    assert "response" in data
