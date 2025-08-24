#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from sqlmodel import Session, SQLModel, select  # noqa: E402
from apps.alchohalt.settings import get_engine  # noqa: E402
from apps.alchohalt.models import Checkin  # noqa: E402
from apps.alchohalt.crypto import encrypt_note, is_encrypted  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        checkins = session.exec(select(Checkin).where(Checkin.note.is_not(None))).all()
        count = 0
        for c in checkins:
            if not is_encrypted(c.note):
                count += 1
                if not args.dry_run:
                    c.note = encrypt_note(c.note)
        if not args.dry_run:
            session.commit()
    msg = "would encrypt" if args.dry_run else "encrypted"
    print(f"{msg} {count} notes")


if __name__ == "__main__":
    main()
