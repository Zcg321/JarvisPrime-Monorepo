import json
import urllib.request


def test_list_tools_v2_schema(server):
    req = urllib.request.Request(
        f"http://127.0.0.1:{server}/list_tools_v2",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    assert any(t["name"] == "dfs_portfolio" and t["version"] == "v1" for t in data["tools"])
    tool = next(t for t in data["tools"] if t["name"] == "dfs_portfolio")
    assert "properties" in tool["args_schema"]
