from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.tools.portfolio_export import portfolio_export


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slate", required=True)
    p.add_argument("--lineups", required=True)
    args = p.parse_args()
    lineups = json.loads(Path(args.lineups).read_text())
    res = portfolio_export(args.slate, lineups, "dk_csv", 0)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
