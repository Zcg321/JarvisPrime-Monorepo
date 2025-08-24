#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel

sys.path.append(str(Path(__file__).resolve().parents[1]))
from apps.alchohalt.settings import get_engine  # noqa: E402
from apps.alchohalt.service import run_notifier  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    now = datetime.now(timezone.utc)
    with Session(engine) as session:
        run_notifier(session, now, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
