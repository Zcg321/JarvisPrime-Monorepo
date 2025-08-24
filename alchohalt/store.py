"""State management for the Alchohalt tracker.

The module keeps a light-weight JSON file to record daily check-ins
and compute streak metrics.  It is intentionally dependency free so the
tracker can run in constrained environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Literal, Optional
import json

AHStatus = Literal["halted", "slipped"]


@dataclass
class AHEntry:
    date: str
    status: AHStatus
    note: Optional[str] = None


@dataclass
class AHState:
    reminder_hour: int = 21
    reminder_minute: int = 0
    entries: Dict[str, AHEntry] = field(default_factory=dict)
    schema_version: int = 1


def load_state(path: Path) -> AHState:
    """Load tracker state from *path* or return a new default state."""
    if path.exists():
        data = json.loads(path.read_text())
        entries = {k: AHEntry(**v) for k, v in data.get("entries", {}).items()}
        return AHState(
            reminder_hour=data.get("reminder_hour", 21),
            reminder_minute=data.get("reminder_minute", 0),
            entries=entries,
            schema_version=data.get("schema_version", 1),
        )
    return AHState()


def save_state(state: AHState, path: Path) -> None:
    """Persist *state* to *path* as JSON."""
    serialised = {
        "reminder_hour": state.reminder_hour,
        "reminder_minute": state.reminder_minute,
        "entries": {k: vars(v) for k, v in state.entries.items()},
        "schema_version": state.schema_version,
    }
    path.write_text(json.dumps(serialised, indent=2))


def checkin(state: AHState, status: AHStatus, note: str | None = None, *, day: Optional[date] = None) -> None:
    """Record a check-in for *day* (defaults to today)."""
    day = day or date.today()
    state.entries[day.isoformat()] = AHEntry(date=day.isoformat(), status=status, note=note)


def _iter_recent_days(start: date, days: int) -> Iterable[date]:
    for i in range(days):
        yield start - timedelta(days=i)


def metrics(state: AHState, *, today: Optional[date] = None) -> Dict[str, object]:
    """Return streak and aggregate metrics for the tracker."""
    today = today or date.today()
    entries = {datetime.fromisoformat(k).date(): v.status for k, v in state.entries.items()}

    streak = 0
    cursor = today
    while entries.get(cursor) == "halted":
        streak += 1
        cursor -= timedelta(days=1)

    last_slip = max((d for d, s in entries.items() if s == "slipped"), default=None)
    halted7 = sum(1 for d in _iter_recent_days(today, 7) if entries.get(d) == "halted")
    halted30 = sum(1 for d in _iter_recent_days(today, 30) if entries.get(d) == "halted")
    series7 = [1 if entries.get(d) == "halted" else 0 for d in reversed(list(_iter_recent_days(today, 7)))]

    return {
        "streak": streak,
        "last_slip_date": last_slip.isoformat() if last_slip else None,
        "halted7": halted7,
        "halted30": halted30,
        "series7": series7,
    }
