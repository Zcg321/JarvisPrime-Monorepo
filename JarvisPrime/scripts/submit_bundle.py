from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import time
from pathlib import Path


def submit(export: str, sim: str) -> Path:
    out_dir = Path("artifacts/exports/dk")
    out_dir.mkdir(parents=True, exist_ok=True)
    export_p = Path(export)
    sim_p = Path(sim)
    try:
        exp_manifest = json.loads(export_p.with_name("MANIFEST.json").read_text())
    except Exception:
        exp_manifest = {}
    export_info = {
        "generated_by": exp_manifest.get("generated_by", "portfolio_export"),
        "slate_id": exp_manifest.get("slate_id", ""),
        "sha256": hashlib.sha256(export_p.read_bytes()).hexdigest(),
        "count": exp_manifest.get("count", 0),
    }
    manifest = {
        "export": export_info,
        "sim_sha256": hashlib.sha256(sim_p.read_bytes()).hexdigest(),
    }
    ts = int(time.time())
    bundle = out_dir / f"bundle_{ts}.tar.gz"
    man_path = out_dir / "MANIFEST.json"
    man_path.write_text(json.dumps(manifest, sort_keys=True))
    with tarfile.open(bundle, "w:gz") as tar:
        tar.add(export_p, arcname=export_p.name)
        tar.add(sim_p, arcname=sim_p.name)
        tar.add(man_path, arcname="MANIFEST.json")
    sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
    (out_dir / "SHA256SUMS").write_text(f"{sha}  {bundle.name}\n")
    print(bundle)
    return bundle


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--sim", required=True)
    args = ap.parse_args()
    submit(args.export, args.sim)
