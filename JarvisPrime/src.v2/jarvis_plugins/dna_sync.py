from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Iterable, List, Dict, Tuple

INDEX_DIR = Path(os.getenv("JARVIS_RAG_DIR", "artifacts/rag")).resolve()
INDEX_DIR.mkdir(parents=True, exist_ok=True)
JSON_INDEX = INDEX_DIR / "index.json"   # always produced
FAISS_INDEX = INDEX_DIR / "index.faiss" # only if faiss+st available
META = INDEX_DIR / "meta.json"

def _read_text_chunks(path: Path) -> Iterable[Tuple[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    # simple paragraph splitter
    parts = re.split(r"\n\s*\n", text)
    for i, p in enumerate(p.strip() for p in parts if p.strip()):
        if len(p) >= 40:
            yield (f"{path.name}#p{i}", p)

def _savepoints() -> Iterable[Tuple[str, str]]:
    sp_dir = Path(os.getenv("JARVIS_SAVEPOINT_DIR", "artifacts/savepoints"))
    if not sp_dir.exists(): return []
    for f in sorted(sp_dir.glob("*.json")):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
            payload = j.get("payload", {})
            text = json.dumps(payload, ensure_ascii=False)
            if text:
                yield (f.name, text)
        except Exception:
            continue

def _anchors() -> Iterable[Tuple[str, str]]:
    a_dir = Path(os.getenv("JARVIS_ANCHORS_DIR", "anchors"))
    if not a_dir.exists(): return []
    for md in a_dir.glob("*.md"):
        yield from _read_text_chunks(md)

def _hash(s: str) -> int:
    # stable 64-bit hash
    import hashlib
    return int(hashlib.sha1(s.encode("utf-8")).hexdigest()[:16], 16)

def _json_only_index(pairs: List[Tuple[str, str]]):
    # create a tiny semantic-less index (hashed shingle counts) that is cheap and offline
    def vec(text: str) -> Dict[str, int]:
        toks = re.findall(r"[A-Za-z]{3,}", text.lower())
        from collections import Counter
        return dict(Counter(toks))
    entries = [{"id": k, "h": _hash(v), "bag": vec(v) if len(v) < 20000 else {}} for k, v in pairs]
    JSON_INDEX.write_text(json.dumps({"entries": entries, "ts": time.time()}, ensure_ascii=False, indent=2), encoding="utf-8")

def _faiss_index(pairs: List[Tuple[str, str]]) -> bool:
    # best-effort embedding + faiss (optional)
    try:
        from sentence_transformers import SentenceTransformer
        import faiss, numpy as np
    except Exception:
        return False
    model_name = os.getenv("JARVIS_ST_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    try:
        m = SentenceTransformer(model_name)
        texts = [t for _, t in pairs]
        vecs = m.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        index = faiss.IndexFlatIP(vecs.shape[1])
        faiss.normalize_L2(vecs)
        index.add(vecs.astype("float32"))
        faiss.write_index(index, str(FAISS_INDEX))
        META.write_text(json.dumps({"model": model_name, "count": len(texts)}, indent=2), encoding="utf-8")
        mapping = [{"id": pairs[i][0]} for i in range(len(pairs))]
        (INDEX_DIR / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False

def rebuild() -> Dict[str, object]:
    pairs = list(_anchors()) + list(_savepoints())
    _json_only_index(pairs)
    ok = _faiss_index(pairs)  # optional
    return {"ok": True, "count": len(pairs), "faiss": bool(ok), "index_dir": str(INDEX_DIR)}

def add_doc(doc_id: str, text: str) -> Dict[str, object]:
    # Append into JSON index; FAISS users should call rebuild for consistency
    try:
        if JSON_INDEX.exists():
            j = json.loads(JSON_INDEX.read_text(encoding="utf-8"))
        else:
            j = {"entries": [], "ts": time.time()}
        j["entries"].append({"id": doc_id, "h": _hash(text), "bag": {}})
        j["ts"] = time.time()
        JSON_INDEX.write_text(json.dumps(j, indent=2), encoding="utf-8")
        return {"ok": True, "appended": doc_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}
