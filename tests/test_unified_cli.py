import subprocess, sys, json


def run_cli(args):
    r = subprocess.run([sys.executable, "-m", "jarvis_plugins.unified_cli"] + args, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def test_cli_recent_runs():
    code, out = run_cli(["recent", "-n", "1"])
    assert code == 0
    assert "items" in out


def test_cli_export_meta(tmp_path):
    code, out = run_cli(["export-int8", "--out", str(tmp_path)])
    assert code == 0
    assert str(tmp_path) in out
