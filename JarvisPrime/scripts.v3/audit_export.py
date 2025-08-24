#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime
import csv
import sys

def mask(val: str) -> str:
    if "@" in val:
        user, domain = val.split("@",1)
        return f"{user[0]}***@{domain}"
    return val

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--from", dest="start", required=True)
    p.add_argument("--to", dest="end", required=True)
    p.add_argument("--format", choices=["json","csv"], default="json")
    p.add_argument("--rotate", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    log_path = Path("logs/audit.jsonl")
    archive = Path("logs/audit.archive.jsonl")
    lines = []
    if log_path.exists():
        lines = log_path.read_text().splitlines()
    keep = []
    out = []
    for line in lines:
        try:
            obj = json.loads(line)
            ts = datetime.fromisoformat(obj["ts"])
            if start <= ts <= end:
                out.append(obj)
                if args.rotate:
                    archive.parent.mkdir(exist_ok=True)
                    with archive.open("a", encoding="utf-8") as f:
                        f.write(line + "\n")
            else:
                keep.append(line)
        except Exception:
            keep.append(line)
    if args.rotate:
        log_path.write_text("\n".join(keep) + ("\n" if keep else ""))
    if args.format == "json":
        print(json.dumps(out))
    else:
        fields = sorted({k for o in out for k in o.keys()})
        writer = csv.DictWriter(sys.stdout, fieldnames=fields)
        writer.writeheader()
        for o in out:
            writer.writerow(o)

if __name__ == "__main__":
    import sys
    main()
