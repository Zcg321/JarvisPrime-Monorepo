import argparse
import hashlib
import json
import tarfile
from pathlib import Path


def restore(src: str, dest: str) -> dict:
    src_path = Path(src)
    dest_path = Path(dest)
    dest_path.mkdir(parents=True, exist_ok=True)
    with tarfile.open(src_path, "r:gz") as tf:
        tf.extractall(dest_path)
    sums_file = src_path.with_name("SHA256SUMS")
    if sums_file.exists():
        for line in sums_file.read_text().splitlines():
            h, rel = line.split("  ")
            fp = dest_path / rel
            if not fp.exists():
                continue
            digest = hashlib.sha256(fp.read_bytes()).hexdigest()
            if digest != h:
                raise ValueError("checksum mismatch")
    return {"restored": len(list(dest_path.rglob('*')))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dest", required=True)
    args = ap.parse_args()
    print(json.dumps(restore(args.src, args.dest)))

if __name__ == "__main__":
    main()
