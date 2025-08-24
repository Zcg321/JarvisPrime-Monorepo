import json
from src.serve import alerts


def test_alerts_index(monkeypatch, tmp_path):
    alert_path = tmp_path / 'alerts.jsonl'
    monkeypatch.setattr(alerts, 'ALERT_PATH', alert_path)
    for i in range(10):
        alerts.log_event('policy', f'p{i}')
    calls = {'n':0}
    orig = alerts._read_all
    def wrapper():
        calls['n'] += 1
        return orig()
    monkeypatch.setattr(alerts, '_read_all', wrapper)
    alerts.get_last()
    summ = alerts.summary()
    assert calls['n'] == 1
    data_file = alert_path.read_text().splitlines()
    assert len(data_file) == 10
    assert summ['type']['policy'] == 10
