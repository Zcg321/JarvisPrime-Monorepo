import json
import urllib.request
import urllib.error
import pytest

from src.serve import locks as locks_mod
from src.data import schedule


def test_get_locks_deterministic(monkeypatch):
    monkeypatch.setattr(schedule, "query", lambda start, end, type=None, path=None: [{"date": "2025-10-25", "slate_id": "SL1", "type": "classic", "teams": []}])
    res = locks_mod.get_locks("2025-10-25", "DK")
    assert res == [{"slate_id": "SL1", "lock_time": "2025-10-25T00:00:00Z"}]


def test_locks_admin_only(server):
    port = server
    url = f"http://127.0.0.1:{port}/locks?date=2025-10-25&site=DK"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer USER_TOKEN"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 403
