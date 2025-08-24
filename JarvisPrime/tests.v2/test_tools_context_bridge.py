from src.tools import context_bridge

def test_context_bridge_search():
    result = context_bridge.search('profit')
    assert 'profit' in result.lower()
