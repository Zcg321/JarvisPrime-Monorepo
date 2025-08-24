import tarfile
import hashlib
import time
from pathlib import Path

TARGETS = [
    "README.md",
    "configs",
    "scripts",
    "data/dna",
    "data/ownership",
    "logs/audit",
    "logs/reports",
    "logs/savepoints",
    "examples/chat",
]


def main() -> None:
    out_dir = Path("artifacts/release")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    tar_path = out_dir / f"jarvisprime_{ts}.tar.gz"
    runme = out_dir / "RUNME.sh"
    config_sha = hashlib.sha256(Path("configs/server.yaml").read_bytes()).hexdigest()
    runme.write_text(
        "#!/bin/sh\nset -e\necho 'version: nova-prime-v2 config_sha: "
        + config_sha
        + "'\nsha256sum -c SHA256SUMS\nif [ -z \"$RUNME_SKIP_SERVER\" ]; then\n  python -m src.serve.server_stub\nfi\n"
    )
    runme.chmod(0o755)
    for d in ["logs/audit", "logs/reports"]:
        Path(d).mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "w:gz") as tar:
        for tgt in TARGETS:
            p = Path(tgt)
            if p.exists():
                tar.add(p)
        tar.add(runme, arcname="RUNME.sh")
    h = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    sums = out_dir / "SHA256SUMS"
    sums.write_text(f"{h}  {tar_path.name}\n")
    assert hashlib.sha256(tar_path.read_bytes()).hexdigest() == h
    print(str(tar_path))

if __name__ == "__main__":
    main()
