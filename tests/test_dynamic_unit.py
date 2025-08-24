import importlib
from src.reflex import policy

def test_unit_size_basic():
    policy.set_token("user1")
    assert policy.unit_size() == 30.0
    policy.set_token("user2")
    assert policy.unit_size() == 30.0
