import glob
import subprocess
import json


def test_offline_snapshot_rerun(tmp_path):
    subprocess.run(["python", "scripts/offline_snapshot.py", "--tag", "test"], check=True)
    files = glob.glob("artifacts/snapshots/offline/*.tar.gz")
    assert files
    subprocess.run(["python", "scripts/offline_rerun.py", "--src", files[0], "--check"], check=True, capture_output=True)
