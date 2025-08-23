from src.reflex.core import Reflex

def test_reflex_choose_action():
    r = Reflex()
    decision = r.choose_action([
        {"weight":1, "source_weight":1, "risk":0.1, "source":"a"},
        {"weight":0.5, "source_weight":1, "risk":0.1, "source":"b"}
    ], affect="confident")
    assert decision
