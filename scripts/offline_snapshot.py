from __future__ import annotations

import argparse
import hashlib
import tarfile
import time
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True)
    args = p.parse_args()
    out_dir = Path("artifacts/snapshots/offline")
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d%H%M%S")
    tar_path = out_dir / f"{args.tag}_{ts}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for pth in ["configs", "logs/savepoints"]:
            pth = Path(pth)
            if pth.exists():
                tar.add(pth)
    sha = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    (out_dir / f"{tar_path.name}.sha256").write_text(sha)
    print(tar_path)


if __name__ == "__main__":
    main()
