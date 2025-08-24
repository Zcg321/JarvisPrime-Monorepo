import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from duet.duet_foreman import run_taskcard, FileSpec, TaskResult
import duet.duet_foreman as df


def test_pr_checks_and_automerge(monkeypatch):
    monkeypatch.setenv('PR_MODE', '1')
    monkeypatch.setenv('AUTOMERGE', '1')

    def fake_codex(envelope):
        return TaskResult(summary='s', files=[FileSpec(path='README.md', op='write', encoding='utf-8', content='x')], commands=[], next_suggestion='')
    monkeypatch.setattr(df, '_codex_call', fake_codex)
    monkeypatch.setattr(df, '_apply_files', lambda files: None)
    monkeypatch.setattr(df, '_run_commands', lambda cmds: True)
    monkeypatch.setattr(df, '_try_push', lambda repo, branch: (True, 'abc123'))
    monkeypatch.setattr(df, 'ensure_workspace', lambda repo, branch: (Path('.'), '', 'https'))

    pr_calls = {}

    def fake_pr(repo, head, base, title, body):
        pr_calls['url'] = 'https://github.com/YOURORG/alchohalt/pull/1'
        return pr_calls['url']

    statuses = {}

    def fake_status(repo, sha, state, context, description, target_url=None):
        statuses['state'] = state

    labels = {}

    def fake_labels(repo, num, labs):
        labels['labels'] = labs

    automerge = {}

    def fake_automerge(repo, num, method='squash'):
        automerge['called'] = True

    monkeypatch.setattr(df, 'ensure_pull_request', fake_pr)
    monkeypatch.setattr(df, 'set_commit_status', fake_status)
    monkeypatch.setattr(df, 'ensure_labels', fake_labels)
    monkeypatch.setattr(df, 'enable_automerge', fake_automerge)

    result = run_taskcard('do', repo='YOURORG/alchohalt')
    assert pr_calls['url'] in result['pr_url']
    assert statuses['state'] == 'success'
    assert labels['labels'] == ['autofeature']
    assert automerge['called']
    assert result['merge'] == 'automerge'
