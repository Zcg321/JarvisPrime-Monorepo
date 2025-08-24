import json
import urllib.request
from pathlib import Path


def test_lineage_api(server):
    port = server
    spdir = Path("logs/savepoints")
    spdir.mkdir(parents=True, exist_ok=True)
    a = {"lineage_id": "A", "event": "t", "ts_iso": "2025-10-25T00:00:00Z"}
    b = {"lineage_id": "B", "parent_id": "A", "event": "t", "ts_iso": "2025-10-25T00:00:01Z"}
    (spdir / "a.json").write_text(json.dumps(a))
    (spdir / "b.json").write_text(json.dumps(b))
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/lineage/B",
        headers={"Authorization": "Bearer ADMIN_TOKEN"},
    )
    data = json.loads(urllib.request.urlopen(req).read().decode())
    assert data["lineage_id"] == "B"
    assert data["ancestors"] and data["ancestors"][0]["lineage_id"] == "A"
    req2 = urllib.request.Request(
        f"http://127.0.0.1:{port}/lineage/ZZ",
        headers={"Authorization": "Bearer ADMIN_TOKEN"},
    )
    try:
        urllib.request.urlopen(req2)
    except urllib.error.HTTPError as e:
        assert e.code == 404
    else:
        assert False
