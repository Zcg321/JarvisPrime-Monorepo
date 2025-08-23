"""Bootstrap replay tests.

MIT License (c) 2025 Zack
"""

import os, subprocess, json, pathlib

def test_bootstrap_replays_experience(tmp_path, monkeypatch):
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    exp_dir = repo_root / 'logs' / 'experience'
    exp_dir.mkdir(parents=True, exist_ok=True)
    sample = exp_dir / 'sample.json'
    sample.write_text('{"msg":"hi"}')
    env = os.environ.copy()
    env['JARVIS_SKIP_BOOTSTRAP_DEPS'] = '1'
    proc = subprocess.run(['bash', str(repo_root / 'scripts' / 'bootstrap_local.sh')], capture_output=True, text=True, env=env)
    sample.unlink()
    assert 'Replayed 1 experience logs' in proc.stdout


def test_bootstrap_skip_replay(monkeypatch):
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env['JARVIS_SKIP_BOOTSTRAP_DEPS'] = '1'
    env['JARVIS_SKIP_REPLAY'] = '1'
    proc = subprocess.run(['bash', str(repo_root / 'scripts' / 'bootstrap_local.sh')], capture_output=True, text=True, env=env)
    assert 'Skipping experience replay' in proc.stdout
