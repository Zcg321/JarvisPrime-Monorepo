import os
import subprocess
import sys
import pathlib


def test_bootstrap_replays_experience(tmp_path):
    repo = pathlib.Path(__file__).resolve().parents[1]
    log_dir = repo / "logs" / "experience"
    log_dir.mkdir(parents=True, exist_ok=True)
    for i in range(2):
        (log_dir / f"{i}.json").write_text("{}")
    env = os.environ.copy()
    env["JARVIS_SKIP_BOOTSTRAP_DEPS"] = "1"
    env["JARVIS_SKIP_REPLAY"] = "0"
    proc = subprocess.run(
        ["bash", "scripts/bootstrap_local.sh"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    import re
    m = re.search(r"Replayed (\d+) experience logs", proc.stdout)
    assert m and int(m.group(1)) >= 2

