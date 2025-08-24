import tarfile
import hashlib
import time
from pathlib import Path

TARGETS = [
    "configs",
    "data/dna",
    "data/ownership",
    "logs/savepoints",
    "logs/ledger",
    "logs/ghosts",
    "logs/reports",
    "logs/perf",
    "README.md",
]

def main() -> None:
    snap_dir = Path("artifacts/snapshots")
    snap_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    tar_path = snap_dir / f"jarvisprime_{ts}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for tgt in TARGETS:
            p = Path(tgt)
            if p.exists():
                tar.add(p)
    h = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    sums = snap_dir / "SHA256SUMS"
    sums.write_text(f"{h}  {tar_path.name}\n")
    assert hashlib.sha256(tar_path.read_bytes()).hexdigest() == h
    print(str(tar_path))

if __name__ == "__main__":
    main()
