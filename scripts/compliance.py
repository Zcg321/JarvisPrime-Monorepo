import argparse
import json
import tarfile
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.serve import alerts
from src.serve import logging as slog

AUDIT_DIR = Path("logs/audit")
SAVEPOINT_DIR = Path("logs/savepoints")
REPORT_DIR = Path("logs/compliance")
ATTEST_DIR = REPORT_DIR / "attestations"
AUDIT_TRAIL_DIR = REPORT_DIR / "audit_trail"


def parse_time(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def load_audit():
    for path in sorted(AUDIT_DIR.glob("*.jsonl")):
        with path.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                yield path, rec


def purge(
    token_id=None,
    since=None,
    until=None,
    simulate=False,
    retention_days: int | None = None,
    confirm: bool = False,
):
    if simulate and not confirm:
        print("simulation requires --confirm", file=sys.stderr)
        sys.exit(1)
    if retention_days is not None:
        cutoff = datetime.utcnow().astimezone(timezone.utc) - timedelta(days=retention_days)
        until = cutoff if until is None else min(until, cutoff)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    SAVEPOINT_DIR.mkdir(parents=True, exist_ok=True)
    ATTEST_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_TRAIL_DIR.mkdir(parents=True, exist_ok=True)
    log_lines = []
    count = 0
    touched = set()
    for path, rec in list(load_audit()):
        ts = parse_time(rec.get("ts_iso"))
        if token_id and rec.get("token_id") != token_id:
            continue
        if since and ts and ts < since:
            continue
        if until and ts and ts > until:
            continue
        line = json.dumps(rec, sort_keys=True)
        log_lines.append(line)
        touched.add(str(path))
        count += 1
        if simulate:
            print(json.dumps({"would_purge": rec}))
            continue
        tomb = {"ts_iso": rec.get("ts_iso"), "tombstone": True}
        lines = []
        with path.open() as f:
            for ln in f:
                obj = json.loads(ln)
                if obj == rec:
                    lines.append(json.dumps(tomb))
                else:
                    lines.append(json.dumps(obj))
        with path.open("w") as f:
            for ln in lines:
                f.write(ln + "\n")
    for sp in SAVEPOINT_DIR.glob("*.json"):
        try:
            data = json.loads(sp.read_text())
        except Exception:
            continue
        ts = parse_time(data.get("ts_iso"))
        if token_id and data.get("token_id") != token_id:
            continue
        if since and ts and ts < since:
            continue
        if until and ts and ts > until:
            continue
        if simulate:
            print(json.dumps({"would_purge_savepoint": data.get("ts_iso")}))
        else:
            sp.write_text(json.dumps({"tombstone": True, "ts_iso": data.get("ts_iso")}))
        log_lines.append(json.dumps(data, sort_keys=True))
        touched.add(str(sp))
        count += 1
    if not simulate:
        alerts.log_event("compliance_purge", "purge executed")
        slog.alert("compliance purge", component="compliance")
    if log_lines:
        ts_now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        hashv = hashlib.sha256("\n".join(log_lines).encode()).hexdigest()
        rec = {
            "ts": ts_now,
            "action": "purge",
            "token_id": token_id,
            "count": count,
            "hash": hashv,
        }
        (ATTEST_DIR / f"receipt_{ts_now}.json").write_text(json.dumps(rec))
        trail = {
            "ts": ts_now,
            "action": "purge",
            "token_id": token_id,
            "files": sorted(touched),
            "receipt_hash": hashv,
        }
        with (AUDIT_TRAIL_DIR / "audit.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(trail) + "\n")


def export(token_id=None, since=None, until=None):
    audits = []
    saves = []
    for _, rec in load_audit():
        ts = parse_time(rec.get("ts_iso"))
        if token_id and rec.get("token_id") != token_id:
            continue
        if since and ts and ts < since:
            continue
        if until and ts and ts > until:
            continue
        audits.append(rec)
    for sp in sorted(SAVEPOINT_DIR.glob("*.json")):
        try:
            data = json.loads(sp.read_text())
        except Exception:
            continue
        ts = parse_time(data.get("ts_iso"))
        if token_id and data.get("token_id") != token_id:
            continue
        if since and ts and ts < since:
            continue
        if until and ts and ts > until:
            continue
        saves.append(data)
    ts_now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    outdir = Path("artifacts/compliance")
    outdir.mkdir(parents=True, exist_ok=True)
    tar_path = outdir / f"export_{ts_now}.tar.gz"
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "audit.json").write_text(json.dumps(audits))
        (tmp_path / "savepoints.json").write_text(json.dumps(saves))
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(tmp_path / "audit.json", arcname="audit.json")
            tar.add(tmp_path / "savepoints.json", arcname="savepoints.json")
    alerts.log_event("compliance_export", "export bundle created")
    slog.alert("compliance export", component="compliance")
    hashv = hashlib.sha256(
        (json.dumps(audits, sort_keys=True) + json.dumps(saves, sort_keys=True)).encode()
    ).hexdigest()
    ATTEST_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": ts_now,
        "action": "export",
        "token_id": token_id,
        "count": len(audits) + len(saves),
        "hash": hashv,
    }
    (ATTEST_DIR / f"receipt_{ts_now}.json").write_text(json.dumps(rec))
    trail = {
        "ts": ts_now,
        "action": "export",
        "token_id": token_id,
        "files": [str(tar_path)],
        "receipt_hash": hashv,
    }
    AUDIT_TRAIL_DIR.mkdir(parents=True, exist_ok=True)
    with (AUDIT_TRAIL_DIR / "audit.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(trail) + "\n")
    print(str(tar_path))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    purge_p = sub.add_parser("purge")
    purge_p.add_argument("--token-id")
    purge_p.add_argument("--since")
    purge_p.add_argument("--until")
    purge_p.add_argument("--simulate", action="store_true")
    purge_p.add_argument("--confirm", action="store_true")
    purge_p.add_argument("--retention-days", type=int)
    export_p = sub.add_parser("export")
    export_p.add_argument("--token-id")
    export_p.add_argument("--since")
    export_p.add_argument("--until")
    args = p.parse_args()
    since = parse_time(getattr(args, "since", None))
    until = parse_time(getattr(args, "until", None))
    if args.cmd == "purge":
        purge(
            args.token_id,
            since,
            until,
            args.simulate,
            args.retention_days,
            args.confirm,
        )
    else:
        export(args.token_id, since, until)


if __name__ == "__main__":
    main()
