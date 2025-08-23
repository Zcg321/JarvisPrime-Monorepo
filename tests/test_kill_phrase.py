import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.serve import server_stub

def test_kill_phrase():
    resp = server_stub.reply(server_stub.KILL)
    assert resp["reply"] == "Acknowledged. Standing by."
