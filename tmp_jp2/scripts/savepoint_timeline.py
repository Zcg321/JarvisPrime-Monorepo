from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime

SAVEPOINT_DIR = Path('logs/savepoints')
REPORT_PATH = Path('logs/reports/savepoint_timeline.json')


def _list_savepoints():
    for p in sorted(SAVEPOINT_DIR.rglob('*.json')):
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        yield data

def main() -> None:
    events = []
    daily = {}
    for sp in _list_savepoints():
        ts = sp.get('ts_iso') or sp.get('ts')
        event = sp.get('event')
        events.append({
            'ts': ts,
            'event': event,
            'affect': sp.get('affect'),
            'bankroll': sp.get('bankroll'),
            'lineage_id': sp.get('lineage_id'),
            'parent_id': sp.get('parent_id'),
        })
        day = (ts or '')[:10]
        daily.setdefault(day, {})
        daily[day][event] = daily[day].get(event, 0) + 1
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({'events': events, 'rollups': daily}, indent=2))

if __name__ == '__main__':
    main()
