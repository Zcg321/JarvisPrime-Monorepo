from __future__ import annotations

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from .logger import log


class SavepointLogger:
    """
    Append-only savepoint logger with ancestry stream.

    ENV overrides:
      JARVIS_SAVEPOINT_DIR: directory for JSON savepoints (default: artifacts/savepoints)
      JARVIS_ANCESTRY_FILE: append-only ancestry file (default: artifacts/ancestry.log)
    """

    def __init__(self,
                 base_dir: Optional[str] = None,
                 ancestry_file: Optional[str] = None) -> None:
        self.base_dir = Path(base_dir or os.getenv("JARVIS_SAVEPOINT_DIR", "artifacts/savepoints")).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.ancestry = Path(ancestry_file or os.getenv("JARVIS_ANCESTRY_FILE", "artifacts/ancestry.log")).resolve()
        self.ancestry.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _ts_str() -> str:
        t = time.time()
        return time.strftime("%Y%m%d_%H%M%S", time.localtime(t)) + f"_{int((t % 1)*1e6):06d}"

    def create(self, payload: Dict[str, Any], tag: str = "savepoint") -> Dict[str, str]:
        data = {"ts": time.time(), "tag": tag, "payload": payload}
        raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha1(raw).hexdigest()[:10]
        fid = f"{self._ts_str()}_{tag}_{digest}.json"
        path = self.base_dir / fid

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        ancestry_row = {"id": fid, "tag": tag, "ts": data["ts"]}
        with self.ancestry.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ancestry_row, ensure_ascii=False) + "\n")
        log('savepoint', {'id': fid, 'tag': tag})

        # optional auto-sync to RAG
        try:
            if os.getenv("JARVIS_DNA_AUTOSYNC", "0") == "1":
                from .dna_sync import add_doc
                add_doc(fid, json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass

        return {"id": fid, "path": str(path)}

    def recent(self, n: int = 10) -> List[str]:
        files = sorted(self.base_dir.glob("*.json"))
        return [p.name for p in files[-n:]]

    def load(self, id_or_path: str) -> Dict[str, Any]:
        p = Path(id_or_path)
        if p.suffix != ".json":
            p = self.base_dir / p.name
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
