import tarfile
import json
from pathlib import Path
import scripts.dashboard as dash


def test_dashboard_export(tmp_path, monkeypatch):
    monkeypatch.setattr(dash, 'OUT', tmp_path)
    dash.main()
    tars = list(tmp_path.glob('dashboard_*.tar.gz'))
    assert tars, 'tarball missing'
    tar_path = tars[0]
    with tarfile.open(tar_path, 'r:gz') as tar:
        names = tar.getnames()
    assert {'dashboard.json', 'dashboard.html', 'sparklines.svg'} <= set(names)
    sha = (tmp_path / 'SHA256SUMS').read_text().split()[0]
    import hashlib
    assert sha == hashlib.sha256(tar_path.read_bytes()).hexdigest()
