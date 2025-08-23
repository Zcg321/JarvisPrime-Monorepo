from src.tools import voice_mirror


def test_keyword_triggers_philosophy():
    out = voice_mirror.reflect("Chasing profit")
    assert "Earn without becoming the enemy." in out
