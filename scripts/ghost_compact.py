import argparse
import hashlib
import json
import tarfile
import time
from pathlib import Path

from src.tools import ghost
from src.serve.metrics import METRICS


def compact(token_id: str, confirm: bool = False) -> Path:
    src = ghost.token_dir(token_id)
    out_root = Path("logs/ghosts/_compacted") / token_id
    out_root.mkdir(parents=True, exist_ok=True)
    snap = out_root / f"snapshot_{int(time.time())}.tar.gz"
    manifest = []
    with ghost.lock_token(token_id):
        files = [p for p in src.glob("*.jsonl") if p.is_file()]
        with tarfile.open(snap, "w:gz") as tar:
            for p in files:
                tar.add(p, arcname=p.name)
                digest = hashlib.sha256(p.read_bytes()).hexdigest()
                manifest.append({"file": p.name, "sha256": digest, "size": p.stat().st_size})
        (out_root / "MANIFEST.json").write_text(json.dumps({"files": manifest}))
        METRICS.ghost_compact_runs += 1
        reclaimed = sum(m["size"] for m in manifest)
        METRICS.ghost_compact_bytes_reclaimed += reclaimed
        if confirm:
            for p in files:
                p.unlink()
    return snap


def main() -> None:  # pragma: no cover
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-id", required=True)
    ap.add_argument("--confirm", action="store_true")
    args = ap.parse_args()
    path = compact(args.token_id, args.confirm)
    print(path)


if __name__ == "__main__":  # pragma: no cover
    main()
