from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import json

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "alchohalt_state.json"


@dataclass
class AHEntry:
    date: str
    status: str
    note: Optional[str] = None


@dataclass
class AHState:
    reminderHour: int = 21
    reminderMinute: int = 0
    entries: Dict[str, AHEntry] = None
    schemaVersion: int = 1

    def __post_init__(self) -> None:
        if self.entries is None:
            self.entries = {}


DEFAULT_STATE = AHState()


def load_state(path: Path = DATA_PATH) -> AHState:
    if path.exists():
        data = json.loads(path.read_text())
        entries = {k: AHEntry(**v) for k, v in data.get("entries", {}).items()}
        return AHState(
            reminderHour=data.get("reminderHour", 21),
            reminderMinute=data.get("reminderMinute", 0),
            entries=entries,
            schemaVersion=data.get("schemaVersion", 1),
        )
    return AHState()


def save_state(state: AHState, path: Path = DATA_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialisable = asdict(state)
    serialisable["entries"] = {k: asdict(v) for k, v in state.entries.items()}
    path.write_text(json.dumps(serialisable, indent=2))


def checkin(status: str, note: Optional[str] = None, *, today: Optional[date] = None) -> AHState:
    today = today or date.today()
    key = today.isoformat()
    state = load_state()
    state.entries[key] = AHEntry(date=key, status=status, note=note)
    save_state(state)
    return state


def metrics(state: Optional[AHState] = None, *, today: Optional[date] = None) -> Dict[str, object]:
    state = state or load_state()
    today = today or date.today()
    entries = state.entries

    # streak calculation
    streak = 0
    cursor = today
    while True:
        key = cursor.isoformat()
        entry = entries.get(key)
        if entry and entry.status == "halted":
            streak += 1
            cursor -= timedelta(days=1)
        else:
            break

    # last slip
    last_slip_date: Optional[str] = None
    for d in sorted(entries):
        if entries[d].status == "slipped":
            last_slip_date = d

    # aggregates
    halted7 = 0
    halted30 = 0
    series7: List[int] = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        key = day.isoformat()
        val = 1 if entries.get(key, AHEntry(key, "slipped")).status == "halted" else 0
        series7.append(val)
    for i in range(30):
        day = today - timedelta(days=i)
        key = day.isoformat()
        if entries.get(key, AHEntry(key, "slipped")).status == "halted":
            halted30 += 1
            if i < 7:
                halted7 += 1

    return {
        "streak": streak,
        "lastSlipDate": last_slip_date,
        "halted7": halted7,
        "halted30": halted30,
        "series7": series7,
    }
