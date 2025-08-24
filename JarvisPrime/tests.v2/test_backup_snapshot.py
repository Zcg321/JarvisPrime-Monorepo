from pathlib import Path
from scripts import backup_snapshot


def test_backup_snapshot(tmp_path, monkeypatch):
    (tmp_path / "configs").mkdir()
    (tmp_path / "data/dna").mkdir(parents=True)
    (tmp_path / "README.md").write_text("x")
    monkeypatch.chdir(tmp_path)
    backup_snapshot.main()
    snaps = list((tmp_path / "artifacts/snapshots").glob("jarvisprime_*.tar.gz"))
    assert snaps
    sums = (tmp_path / "artifacts/snapshots/SHA256SUMS").read_text()
    assert snaps[0].name in sums
