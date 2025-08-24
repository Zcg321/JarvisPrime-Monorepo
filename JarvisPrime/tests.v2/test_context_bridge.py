import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools import context_bridge
from src.core import anchors

ANCHORS = anchors.load_all()

def test_search():
    snippet = context_bridge.search("everything matters", ANCHORS)
    assert "everything matters" in snippet.lower()
