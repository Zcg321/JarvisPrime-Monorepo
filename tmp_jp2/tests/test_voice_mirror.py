import sys, pathlib

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.tools.voice_mirror import reflect


def test_reflect_appends_philosophy():
    text = "We must seek profit without corruption."
    out = reflect(text)
    assert "profit without corruption" in out.lower()
    # ensure philosophy snippet appended
    assert "Earn without becoming the enemy." in out


def test_reflect_affect_bias():
    text = "I feel nervous"
    out = reflect(text, affect="anxious")
    assert "ease your mind" in out

