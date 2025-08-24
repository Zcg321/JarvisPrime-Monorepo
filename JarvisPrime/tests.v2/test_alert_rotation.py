from pathlib import Path
from src.serve import alerts, metrics


def test_alert_rotation(tmp_path):
    alerts.ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
    for p in alerts.ALERT_PATH.parent.glob('alerts.jsonl*'):
        p.unlink()
    big = 'x' * (1024 * 1024)
    for _ in range(11):
        alerts.log_event('policy', big)
    assert alerts.ALERT_PATH.with_name('alerts.jsonl.1').exists()
    snap = metrics.METRICS.snapshot()
    assert snap['alerts_rotations'] > 0
    assert snap['alerts_file_size'] <= 10 * 1024 * 1024
