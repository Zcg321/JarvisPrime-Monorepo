import tarfile
from pathlib import Path
import subprocess
import os


def test_release_bundle(tmp_path):
    env = dict(os.environ)
    env["PYTHONPATH"] = "."
    subprocess.check_call(["python", "scripts/release_bundle.py"], env=env)
    release_dir = Path("artifacts/release")
    tars = sorted(release_dir.glob("jarvisprime_*.tar.gz"))
    assert tars, "tarball not created"
    tar_path = tars[-1]
    sums = release_dir / "SHA256SUMS"
    assert sums.exists()
    with tarfile.open(tar_path, "r:gz") as tar:
        runme = tar.getmember("RUNME.sh")
        assert runme.mode & 0o111
    # idempotent rerun
    subprocess.check_call(["python", "scripts/release_bundle.py"], env=env)
