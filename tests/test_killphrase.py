from src.core import anchors

def test_killphrase_extraction():
    data = anchors.load_all()
    assert anchors.kill_phrase(data['boot']) == 'lights out, jarvis'
