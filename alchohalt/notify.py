"""Reminder scheduling for Alchohalt.

Real notification scheduling requires platform integration.  The
`schedule_daily` function here merely logs the intent to schedule a
reminder.  It can be replaced by a proper scheduler in the future.
"""

from datetime import time


def schedule_daily(hour: int, minute: int) -> str:
    """Return a human-readable description of the scheduled reminder."""
    t = time(hour=hour, minute=minute)
    message = f"Reminder scheduled daily at {t.strftime('%H:%M')}"
    print(message)
    return message
