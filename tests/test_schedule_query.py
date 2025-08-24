from src.data import schedule
from src.serve.server_stub import ResultsArgs  # just to ensure import (unused) -> but not needed?; skip


def test_query_basic():
    res = schedule.query("2025-10-25", "2025-10-25", "classic", path="data/schedule/samples/2025-10-25.json")
    assert res and res[0]["slate_id"] == "DK_NBA_2025-10-25_MAIN"


def test_bad_schema(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("date,slate_id,type\n2025-10-25,ID,classic\n")
    try:
        schedule.query("2025-10-25", "2025-10-25", path=p)
    except ValueError as e:
        assert "missing" in str(e)
    else:
        assert False
