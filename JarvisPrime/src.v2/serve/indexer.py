import json
from pathlib import Path
from typing import Dict


class _Index:
    def __init__(self, path: Path):
        self.path = path
        self.rows = 0
        self.inode = None
        self.mtime = None
        self.rebuilt = 0

    def ensure(self):
        try:
            st = self.path.stat()
            inode, mtime = st.st_ino, st.st_mtime
        except FileNotFoundError:
            inode = mtime = None
        if inode != self.inode or mtime != self.mtime:
            self.rebuild()
            return
        try:
            with self.path.open() as f:
                for line in f:
                    json.loads(line)
            self.rows = sum(1 for _ in self.path.open())
        except Exception:
            self.rebuild()

    def rebuild(self):
        self.rows = 0
        if self.path.exists():
            with self.path.open() as f:
                for line in f:
                    try:
                        json.loads(line)
                        self.rows += 1
                    except Exception:
                        continue
            st = self.path.stat()
            self.inode, self.mtime = st.st_ino, st.st_mtime
        else:
            self.inode = self.mtime = None
        self.rebuilt += 1


INDEXES: Dict[str, _Index] = {
    'alerts': _Index(Path('logs/alerts.jsonl')),
    'audit': _Index(Path('logs/audit/audit.jsonl')),
    'lineage': _Index(Path('logs/savepoints/index.jsonl')),
    'metrics': _Index(Path('logs/metrics/requests.jsonl')),
}


def status() -> Dict[str, Dict[str, int]]:
    out = {}
    for name, idx in INDEXES.items():
        idx.ensure()
        out[name] = {'rows': idx.rows, 'rebuilt': idx.rebuilt}
    return out


def rebuild(which: str) -> Dict[str, Dict[str, int]]:
    names = INDEXES.keys() if which == 'all' else [which]
    out = {}
    for name in names:
        idx = INDEXES.get(name)
        if not idx:
            continue
        idx.rebuild()
        out[name] = {'rows': idx.rows, 'rebuilt': idx.rebuilt}
    return out
