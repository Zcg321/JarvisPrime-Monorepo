import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]

EXCLUDES = (
    'logs/', 'artifacts/', '.git/', 'node_modules/', '__pycache__/'
)

def scan_file_map(max_files: int = 8000, max_bytes_per_file: int = 0) -> List[Dict]:
    """Return list of repo files with size and last commit ts."""
    try:
        out = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, cwd=ROOT, check=True).stdout
    except Exception:
        return []
    files = out.splitlines()
    results = []
    for f in files:
        if any(f.startswith(ex) for ex in EXCLUDES):
            continue
        p = ROOT / f
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        try:
            ts = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', f], capture_output=True, text=True, cwd=ROOT).stdout.strip()
            ts_int = int(ts) if ts.isdigit() else 0
        except Exception:
            ts_int = 0
        results.append({'path': f, 'size': size, 'last_commit': ts_int})
        if len(results) >= max_files:
            break
    return results

def head_changes(n: int = 3) -> List[Dict]:
    try:
        out = subprocess.run(['git', 'log', f'-n{n}', '--pretty=format:%h|%ad|%s', '--date=iso'],
                             capture_output=True, text=True, cwd=ROOT, check=True).stdout
    except Exception:
        return []
    entries = []
    for line in out.splitlines():
        parts = line.split('|', 2)
        if len(parts) == 3:
            entries.append({'sha': parts[0], 'date': parts[1], 'subject': parts[2]})
    return entries

def head_diff(paths: Optional[List[str]] = None, max_bytes: int = 100_000) -> str:
    args = ['git', 'diff', 'HEAD~1', 'HEAD']
    if paths:
        args += ['--'] + list(paths)
    try:
        proc = subprocess.run(args, capture_output=True, cwd=ROOT)
        diff = proc.stdout
    except Exception:
        return '(none)'
    if proc.returncode != 0 and not diff:
        return '(none)'
    if len(diff) > max_bytes:
        diff = diff[:max_bytes]
    return diff.decode('utf-8', errors='replace')

def read_hot_files(paths: List[str], max_bytes_each: int = 30_000) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in paths:
        fp = ROOT / p
        if not fp.exists():
            continue
        try:
            data = fp.open('rb').read(max_bytes_each)
            out[p] = data.decode('utf-8', errors='replace')
        except Exception:
            continue
    return out
