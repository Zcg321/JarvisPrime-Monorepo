import argparse
import json
import csv
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone


def parse_time(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def iter_records():
    for path in sorted(Path("logs/audit").glob("*.jsonl")):
        with path.open() as f:
            for line in f:
                try:
                    yield json.loads(line)
                except Exception:
                    continue


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token-id")
    p.add_argument("--tool")
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--format", choices=["json", "csv"], default="json")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()
    since = parse_time(args.since)
    until = parse_time(args.until)
    out = []
    for rec in iter_records():
        ts = parse_time(rec.get("ts_iso"))
        if args.token_id and rec.get("token_id") != args.token_id:
            continue
        if args.tool and rec.get("tool") != args.tool:
            continue
        if since and ts and ts < since:
            continue
        if until and ts and ts > until:
            continue
        out.append(rec)
    if args.summary:
        tool_counts = Counter(r.get("tool") for r in out)
        token_counts = Counter(r.get("token_id") for r in out)
        summary = {
            "per_tool": dict(tool_counts),
            "per_token": dict(token_counts),
            "total": len(out),
        }
        print(json.dumps(summary))
    elif args.format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(["ts", "tool", "token_id", "result_status"])
        for r in out:
            writer.writerow([r.get("ts_iso"), r.get("tool"), r.get("token_id"), r.get("result_status")])
    else:
        print(json.dumps(out))


if __name__ == "__main__":
    main()
