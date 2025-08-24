from __future__ import annotations

import argparse
import json
from typing import Any

from . import checkin, metrics, schedule


def main(argv: list[str] | None = None) -> int:
    """Simple command line interface for Alchohalt.

    Supports logging check-ins, scheduling reminders, and printing streak
    metrics. Example usage::

        python -m alchohalt.cli checkin halted --note "Feeling good"
        python -m alchohalt.cli stats
        python -m alchohalt.cli schedule 21:00
    """

    parser = argparse.ArgumentParser(prog="alchohalt")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_checkin = sub.add_parser("checkin", help="record a halted or slipped day")
    p_checkin.add_argument("status", choices=["halted", "slipped"])
    p_checkin.add_argument("--note", default=None, help="optional note (120 chars)")

    sub.add_parser("stats", help="print current streak metrics as JSON")

    p_sched = sub.add_parser("schedule", help="schedule a daily reminder")
    p_sched.add_argument("time", help="HH:MM 24-hour time")

    args = parser.parse_args(argv)
    if args.cmd == "checkin":
        checkin(args.status, note=args.note)
        return 0
    if args.cmd == "stats":
        data: dict[str, Any] = metrics()
        print(json.dumps(data, indent=2))
        return 0
    if args.cmd == "schedule":
        hour, minute = map(int, args.time.split(":"))
        schedule(hour, minute)
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
