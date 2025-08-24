from src.tools import uptake, plan
from src.core import anchors
import src.train.uptake as base_uptake

def test_uptake_record_and_replay(tmp_path, monkeypatch):
    monkeypatch.setattr(base_uptake, 'LOG_DIR', tmp_path)
    path = uptake.record({'a':1})
    assert path
    replayed = uptake.replay()
    assert replayed[0]['a']==1

def test_plan_steps():
    steps = plan.generate('', anchors.load_all())
    assert steps
