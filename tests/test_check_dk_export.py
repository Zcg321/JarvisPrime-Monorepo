import json
from scripts import check_dk_export


def test_dk_check(tmp_path):
    good = tmp_path / "good.csv"
    good.write_text("PG,SG,SF,PF,C,G,F,UTIL\n")
    report = check_dk_export.check(str(good))
    assert report["ok"]
    bad = tmp_path / "bad.csv"
    bad.write_text("X,Y\n1,2\n")
    report2 = check_dk_export.check(str(bad))
    assert not report2["ok"]
    empty = tmp_path / "empty.csv"
    empty.write_text("\n")
    report3 = check_dk_export.check(str(empty))
    assert report3["ok"] and report3["count"] == 0
