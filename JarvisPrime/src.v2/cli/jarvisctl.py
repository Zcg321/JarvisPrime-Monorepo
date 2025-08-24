"""Minimal CLI wrappers for common tools."""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

from src.tools import dfs_portfolio, dfs_showdown
from src.tools.slate_sim import run as slate_sim_run
from src.tools.roi_report import generate as roi_generate


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="jarvisctl")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_port = sub.add_parser("dfs-portfolio")
    p_port.add_argument("--n", type=int, default=1)

    p_show = sub.add_parser("showdown")
    p_show.add_argument("--slate", required=True)

    p_roi = sub.add_parser("roi-report")
    p_roi.add_argument("--days", type=int, default=60)

    p_sim = sub.add_parser("slate-sim")
    p_sim.add_argument("--csv", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "dfs-portfolio":
        res = dfs_portfolio.build([{"id": "SIM", "type": "classic"}], args.n)
        _print(res)
    elif args.cmd == "showdown":
        res = dfs_showdown.showdown_lineup([], slate_id=args.slate)
        _print(res)
    elif args.cmd == "roi-report":
        _print(roi_generate(args.days))
    elif args.cmd == "slate-sim":
        _print(slate_sim_run([], args.csv))


if __name__ == "__main__":
    main()
