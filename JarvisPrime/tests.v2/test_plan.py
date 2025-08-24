from src.core import anchors
from src.tools import plan


def test_plan_default():
    anc = anchors.load_all()
    steps = plan.generate("", anc)
    assert len(steps) >= len(anc["ascension"]["reversed_path"][0]["actions"])
    assert {"phase", "action"} <= steps[0].keys()


def test_plan_query_keyword():
    anc = anchors.load_all()
    steps = plan.generate("Voice Mirror", anc)
    assert any("Voice Mirror" in s["action"] for s in steps)
