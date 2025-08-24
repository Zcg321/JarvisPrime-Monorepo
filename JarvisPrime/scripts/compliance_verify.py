import json
import hashlib
from pathlib import Path

TRAIL = Path("logs/compliance/audit_trail/audit.jsonl")
REPORT = Path("logs/compliance/verify_report.json")


def verify() -> None:
    details = []
    ok = True
    if TRAIL.exists():
        for ln in TRAIL.open():
            try:
                rec = json.loads(ln)
            except Exception:
                continue
            files = [Path(f) for f in rec.get("files", [])]
            data = []
            for p in files:
                try:
                    data.append(Path(p).read_text())
                except Exception:
                    ok = False
                    details.append({"receipt_hash": rec.get("receipt_hash"), "status": "missing"})
                    break
            else:
                digest = hashlib.sha256("".join(data).encode()).hexdigest()
                status = "ok" if digest == rec.get("receipt_hash") else "mismatch"
                if status != "ok":
                    ok = False
                details.append({"receipt_hash": rec.get("receipt_hash"), "status": status})
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"status": "ok" if ok else "mismatch", "details": details}))
    print(str(REPORT))


if __name__ == "__main__":
    verify()
