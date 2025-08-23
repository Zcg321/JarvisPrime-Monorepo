import src.serve.server_stub as stub

def test_list_tools_contains_surged():
    res = stub.router({"tool": "list_tools", "args": {}})
    assert "surgecell" in res["tools"]
    assert res["tools"]["surgecell"].startswith("Return")
