import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.serve.server_stub import JSON_ONLY

def test_ok():
    assert JSON_ONLY.match('{"tool":"x","args":{"a":1}}')

def test_bad():
    assert not JSON_ONLY.match('mix {"tool":"x","args":{}} prose')
