import json
from pathlib import Path
from scripts.savepoint_timeline import main, REPORT_PATH, SAVEPOINT_DIR


def test_timeline(tmp_path, monkeypatch):
    monkeypatch.setattr('scripts.savepoint_timeline.SAVEPOINT_DIR', tmp_path)
    monkeypatch.setattr('scripts.savepoint_timeline.REPORT_PATH', tmp_path/'out.json')
    s1 = tmp_path / 'a.json'
    s2 = tmp_path / 'b.json'
    s1.write_text(json.dumps({'event':'x','ts_iso':'2025-01-01T00:00:00'}))
    s2.write_text(json.dumps({'event':'y','ts_iso':'2025-01-01T01:00:00'}))
    main()
    data = json.loads((tmp_path/'out.json').read_text())
    assert data['events'][0]['event'] == 'x'
    assert data['rollups']['2025-01-01']['x'] == 1
