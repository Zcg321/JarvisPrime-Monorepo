import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Dict, List

DB_PATH = Path(os.environ.get("ALCHOHALT_DB", "data/alchohalt.db"))


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT)")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS entries (date TEXT PRIMARY KEY, status TEXT, note TEXT)"
    )
    conn.commit()
    return conn


def schedule(hour: int = 21, minute: int = 0) -> Dict[str, int]:
    """Persist desired reminder time in the database."""
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO state(key, value) VALUES('reminder_hour', ?)", (str(hour),)
        )
        cur.execute(
            "REPLACE INTO state(key, value) VALUES('reminder_minute', ?)", (str(minute),)
        )
        conn.commit()
    return {"reminder_hour": hour, "reminder_minute": minute}


def _write_entry(day: str, status: str, note: Optional[str] = None) -> None:
    with _conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "REPLACE INTO entries(date, status, note) VALUES(?, ?, ?)",
            (day, status, note),
        )
        conn.commit()


def checkin(status: str, note: Optional[str] = None) -> Dict[str, str]:
    today = date.today().isoformat()
    _write_entry(today, status, note)
    return {"date": today, "status": status, "note": note}


def _fetch_entries() -> Dict[str, Dict[str, str]]:
    with _conn() as conn:
        cur = conn.cursor()
        rows = cur.execute("SELECT date, status, note FROM entries").fetchall()
    return {d: {"status": s, "note": n} for d, s, n in rows}


def metrics(today: Optional[date] = None) -> Dict[str, object]:
    today = today or date.today()
    entries = _fetch_entries()
    streak = 0
    for i in range(0, 365):
        d = today - timedelta(days=i)
        e = entries.get(d.isoformat())
        if e and e.get("status") == "halted":
            streak += 1
        else:
            break

    halted7 = 0
    halted30 = 0
    series7: List[int] = []
    for i in range(0, 30):
        d = today - timedelta(days=i)
        e = entries.get(d.isoformat())
        halted = 1 if e and e.get("status") == "halted" else 0
        if i < 7:
            series7.insert(0, halted)
            halted7 += halted
        halted30 += halted

    last_slip = None
    for d_str, e in entries.items():
        if e.get("status") == "slipped":
            if not last_slip or d_str > last_slip:
                last_slip = d_str

    return {
        "streak": streak,
        "lastSlipDate": last_slip,
        "halted7": halted7,
        "halted30": halted30,
        "series7": series7,
    }
