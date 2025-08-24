import tarfile
import hashlib
from pathlib import Path
from scripts import backup_restore


def test_restore_roundtrip(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    f = src_dir / "a.txt"
    f.write_text("hi")
    tar_path = tmp_path / "snap.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(f, arcname="a.txt")
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    (tmp_path / "SHA256SUMS").write_text(f"{h}  a.txt\n")
    dest = tmp_path / "out"
    res = backup_restore.restore(str(tar_path), str(dest))
    assert (dest / "a.txt").read_text() == "hi"
    assert res["restored"] > 0
