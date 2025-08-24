import os
import subprocess
import importlib


def test_ensure_workspace(monkeypatch, tmp_path):
    module = importlib.import_module('duet.workspaces')
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'WORKSPACES', tmp_path / 'workspaces')

    calls = []

    def fake_run(cmd, *a, **kw):
        calls.append(cmd)
        class Res:
            returncode = 0
            stdout = ''
        return Res()

    monkeypatch.setattr(subprocess, 'run', fake_run)
    os.environ['GITHUB_TOKEN_OWNER__REPO'] = 'tok'
    path, url, mode = module.ensure_workspace('owner/repo', 'main')
    assert path == tmp_path / 'workspaces' / 'owner__repo'
    assert mode == 'https'
    path.mkdir(parents=True, exist_ok=True)
    module.ensure_workspace('owner/repo', 'main')
    clone_calls = [c for c in calls if c[:2] == ['git', 'clone']]
    assert len(clone_calls) == 1
    set_url_calls = [c for c in calls if c[:3] == ['git', 'remote', 'set-url']]
    assert any('tok' in ' '.join(c) for c in set_url_calls)
    del os.environ['GITHUB_TOKEN_OWNER__REPO']
    calls.clear()
    os.environ['GT_TOKEN'] = 'fallback'
    module.ensure_workspace('owner/repo', 'main')
    set_url_calls = [c for c in calls if c[:3] == ['git', 'remote', 'set-url']]
    assert any('fallback' in ' '.join(c) for c in set_url_calls)
