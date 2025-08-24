import sys
import pathlib
import subprocess
import time
import json
import urllib.request

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.reflex import core as reflex_core


def test_policy_blocks(monkeypatch):
    monkeypatch.setattr(reflex_core, "POLICY", {"unit_fraction": 0.1, "allow_when_affect": ["calm"]})
    r = reflex_core.Reflex()
    bad = {"bankroll": 100, "wager": 20, "affect": "anxious"}
    check = r.self_check(bad)
    assert check["blocked"] and check["reason"] == "affect"
    good = {"bankroll": 100, "wager": 5, "affect": "calm"}
    check2 = r.self_check(good)
    assert not check2["blocked"]


def test_health_exposes_policy(server):
    with urllib.request.urlopen(f"http://127.0.0.1:{server}/health", timeout=5) as r:
        data = json.loads(r.read().decode())
    assert "policy" in data and "unit_fraction" in data["policy"]
