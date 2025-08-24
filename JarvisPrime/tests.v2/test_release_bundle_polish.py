import tarfile, subprocess, os
from pathlib import Path


def test_release_bundle_contains_audit(tmp_path):
    subprocess.check_call(["python", "scripts/release_bundle.py"], cwd=Path.cwd())
    out_dir = Path("artifacts/release")
    tar_path = sorted(out_dir.glob("jarvisprime_*.tar.gz"))[-1]
    with tarfile.open(tar_path, "r:gz") as tar:
        names = tar.getnames()
        assert any(n.startswith("logs/audit") for n in names)
        assert any(n.startswith("logs/reports") for n in names)
    env = os.environ.copy(); env["RUNME_SKIP_SERVER"] = "1"
    out = subprocess.check_output(["sh", "RUNME.sh"], env=env, cwd=out_dir)
    assert b"version:" in out and b"config_sha" in out
