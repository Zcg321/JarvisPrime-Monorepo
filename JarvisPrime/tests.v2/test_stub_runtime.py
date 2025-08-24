import json
from src.serve.server_stub import reply, KILL
from src.train import uptake


def test_kill_phrase_response():
    assert reply(KILL)["reply"] == "Acknowledged. Standing by."


def test_recall_tool_returns_experience(tmp_path):
    uptake.LOG_DIR = tmp_path  # redirect logging
    uptake.record({"user": "hi", "response": {"reply": "yo"}})
    out = reply('{"tool":"recall","args":{"n":1}}')
    assert out["tool_result"]["experiences"], "recall should return experiences"


def test_experience_search_tool(tmp_path):
    uptake.LOG_DIR = tmp_path
    uptake.record({"user": "alpha", "response": {"reply": "hi"}})
    uptake.record({"user": "beta", "response": {"reply": "yo"}})
    out = reply('{"tool":"experience_search","args":{"query":"alpha"}}')
    exps = out["tool_result"]["experiences"]
    assert len(exps) == 1 and exps[0]["user"] == "alpha"


def test_anchor_snippet_lookup():
    out = reply("everything matters")
    assert "everything matters" in out["reply"].lower()


def test_shell_tool_call():
    out = reply('{"tool":"shell","args":{"cmd":"echo hi"}}')
    assert out["tool_result"]["stdout"] == "hi"


def test_hardware_safety_tool():
    out = reply('{"tool":"hardware_safety","args":{}}')
    result = out["tool_result"]
    assert "info" in result and "config" in result


def test_reflex_feedback_tool():
    out = reply('{"tool":"reflex_feedback","args":{"source":"dfs","success":true}}')
    assert out["tool_result"]["bias"] > 1.0


def test_experience_stats_tool(tmp_path):
    uptake.LOG_DIR = tmp_path
    uptake.record({"user": "alpha", "response": {"reply": "hi"}})
    out = reply('{"tool":"experience_stats","args":{}}')
    stats = out["tool_result"]
    assert stats["count"] == 1 and stats["last_ts"] > 0
