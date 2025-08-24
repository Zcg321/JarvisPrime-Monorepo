from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import json


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    src = Path(args.src)
    if args.check:
        sha_path = src.with_suffix(src.suffix + ".sha256")
        if sha_path.exists():
            actual = hashlib.sha256(src.read_bytes()).hexdigest()
            expected = sha_path.read_text().strip()
            ok = actual == expected
            print(json.dumps({"ok": ok}))
        else:
            print(json.dumps({"ok": False, "reason": "missing_sha"}))


if __name__ == "__main__":
    main()
