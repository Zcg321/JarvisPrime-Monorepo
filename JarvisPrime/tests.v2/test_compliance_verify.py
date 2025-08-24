import json
import hashlib
import subprocess
from pathlib import Path


def _prep():
    base = Path("logs/compliance")
    attest = base / "attestations"
    trail = base / "audit_trail"
    attest.mkdir(parents=True, exist_ok=True)
    trail.mkdir(parents=True, exist_ok=True)
    sample = base / "sample.txt"
    sample.write_text("hello")
    h = hashlib.sha256("hello".encode()).hexdigest()
    (trail / "audit.jsonl").write_text(json.dumps({"files": [str(sample)], "receipt_hash": h}) + "\n")
    return sample


def test_compliance_verify():
    sample = _prep()
    subprocess.run(["python", "scripts/compliance_verify.py"], check=True)
    report = json.loads(Path("logs/compliance/verify_report.json").read_text())
    assert report["status"] == "ok"
    sample.write_text("tamper")
    subprocess.run(["python", "scripts/compliance_verify.py"], check=True)
    report = json.loads(Path("logs/compliance/verify_report.json").read_text())
    assert report["status"] == "mismatch"
