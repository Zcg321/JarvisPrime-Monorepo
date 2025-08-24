import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from duet import context


def test_scan_file_map_excludes():
    files = context.scan_file_map()
    assert any(f['path'] == 'README.md' for f in files)
    assert not any(f['path'].startswith('logs/') for f in files)
    first = files[0]
    assert 'size' in first and 'last_commit' in first


def test_head_diff_no_crash(tmp_path, monkeypatch):
    subprocess.run(['git','init'], cwd=tmp_path, check=True)
    (tmp_path/'a.txt').write_text('hi')
    subprocess.run(['git','add','a.txt'], cwd=tmp_path, check=True)
    subprocess.run(['git','commit','-m','init'], cwd=tmp_path, check=True)
    monkeypatch.setattr(context, 'ROOT', tmp_path)
    diff = context.head_diff()
    assert isinstance(diff, str)


def test_read_hot_files():
    out = context.read_hot_files(['README.md','nope.txt'], max_bytes_each=10)
    assert 'README.md' in out
    assert 'nope.txt' not in out
    assert len(out['README.md']) <= 10
