import asyncio
import base64
import json
import os
import subprocess
import shlex
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

import requests
import yaml

from . import context as ctx
from .context import scan_file_map, head_changes, head_diff, read_hot_files
from .workspaces import ensure_workspace, push_current
from bridge.github_api import ensure_pull_request, set_commit_status, ensure_labels, enable_automerge
from bridge.policy import validate_plan, get_limits

ROOT = Path(__file__).resolve().parents[1]
FOREMAN = ROOT / "foreman"
BATON_FILE = FOREMAN / "baton.json"
ARTIFACTS = ROOT / "artifacts"
PATCHES = ARTIFACTS / "patches"
CONFIG = yaml.safe_load((FOREMAN / "config.yaml").read_text())
MAX_FILES = CONFIG.get("max_files_touched", 15)
CTX_CFG = CONFIG.get(
    "context",
    {
        "include_repo_map": True,
        "include_hot_files": True,
        "include_recent_log": True,
        "include_last_diff": True,
        "max_files_listed": 8000,
        "hot_max_bytes_each": 30000,
        "diff_max_bytes": 100000,
    },
)
CONTRACT_TEXT = (ROOT / "CONTRACT.md").read_text()


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class FileSpec:
    path: str
    op: str
    encoding: str
    content: str = ""


@dataclass
class TaskResult:
    summary: str
    files: List[FileSpec]
    commands: List[str]
    next_suggestion: str


def redact(s: str) -> str:
    if not s:
        return s
    deny = ["OPENAI_API_KEY", "GT_TOKEN", "ALC_", "TWILIO_", "FOREMAN_SHARED_TOKEN"]
    for key in deny:
        s = re.sub(rf"({key}[A-Z0-9_]*\s*[=:]\s*)([^\s]+)", r"\1***", s, flags=re.IGNORECASE)
    return s


def _build_envelope(task_card: str, repo: str | None, branch: str | None) -> str:
    parts = [f"repo={repo or '(none)'} branch={branch or '(none)'}"]
    if CTX_CFG.get("include_repo_map", True):
        fm = scan_file_map(CTX_CFG.get("max_files_listed", 8000))
        lines = [f"{f['path']} · {f['size']} · {f['last_commit']}" for f in fm]
        parts.append("== REPO MAP ==\n" + "\n".join(lines))
    if CTX_CFG.get("include_hot_files", True):
        hot_paths = [
            "README.md",
            "STATUS.md",
            "pyproject.toml",
            "requirements.txt",
            ".github/workflows/ci.yml",
            "apps/alchohalt/app.py",
            "apps/alchohalt/service.py",
            "apps/alchohalt/schemas.py",
            "apps/alchohalt/models.py",
            "apps/alchohalt/ui.py",
        ]
        hot = read_hot_files(hot_paths, CTX_CFG.get("hot_max_bytes_each", 30000))
        snippets = []
        for p, content in hot.items():
            snippets.append(f"```{p} ({len(content.encode('utf-8'))} bytes)\n{content}\n```")
        parts.append("== HOT FILE EXCERPTS ==\n" + "\n".join(snippets))
    if CTX_CFG.get("include_recent_log", True):
        log_entries = head_changes(3)
        lines = [f"{e['sha']} {e['date']} {e['subject']}" for e in log_entries]
        parts.append("== RECENT LOG ==\n" + "\n".join(lines))
    if CTX_CFG.get("include_last_diff", True):
        diff = head_diff(max_bytes=CTX_CFG.get("diff_max_bytes", 100000))
        parts.append("== LAST DIFF (HEAD~1..HEAD) ==\n" + (diff or "(none)"))
    baton_excerpt = ""
    if BATON_FILE.exists():
        try:
            baton_excerpt = json.loads(BATON_FILE.read_text()).get("summary", "")
        except Exception:
            baton_excerpt = ""
    parts.append("== BATON ==\n" + baton_excerpt)
    anchor_names = [p.name for p in (ROOT / "core" / "jarvisprime").glob("*")]
    parts.append("== ANCHORS ==\n" + ", ".join(anchor_names))
    parts.append("== TASK CARD ==\n" + task_card)
    return "\n\n".join(parts)


def _codex_call(envelope: str) -> TaskResult:
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("CODEX_MODEL", CONFIG["models"]["codex"])
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    system = (
        "You are Codex executor. Produce only one JSON object per CONTRACT.md. "
        f"Foreman identity: foreman_id=jarvis-foreman, conversation_hint=continuum-foreman-thread. "
        f"Small-diff policy: touch ≤{MAX_FILES} files, update tests, docs, STATUS.md. "
        "Never print secrets. Reject absolute or '..' paths."
    )
    user = f"{CONTRACT_TEXT}\n\n{envelope}\nRespond with exactly one JSON object and nothing else."
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }
    r = requests.post(url, headers=headers, json=data, timeout=300)
    r.raise_for_status()
    j = r.json()
    raw = j["choices"][0]["message"]["content"]
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    (ARTIFACTS / f"codex_out_{ts}.txt").write_text(redact(raw))
    payload = json.loads(raw)
    files = [FileSpec(**f) for f in payload.get("files", [])]
    return TaskResult(
        summary=payload.get("summary", ""),
        files=files,
        commands=payload.get("commands", []),
        next_suggestion=payload.get("next_suggestion", ""),
    )


def _safe_path(p: str) -> Path:
    rel = Path(p)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("unsafe path")
    return ROOT / rel


def _apply_files(files: List[FileSpec]) -> None:
    if len(files) > MAX_FILES:
        raise ValueError("too many files")
    for f in files:
        full = _safe_path(f.path)
        full.parent.mkdir(parents=True, exist_ok=True)
        data = f.content
        if f.encoding == "base64":
            data_bytes = base64.b64decode(data.encode())
        else:
            data_bytes = data.encode()
        if f.op == "write":
            full.write_bytes(data_bytes)
        elif f.op == "append":
            with open(full, "ab") as fp:
                fp.write(data_bytes)
        elif f.op == "delete":
            if full.exists():
                full.unlink()
        else:
            raise ValueError("bad op")


def _run_commands(cmds: List[str]) -> bool:
    for c in cmds:
        res = subprocess.run(c, shell=True)
        if res.returncode != 0:
            return False
    return True


def _try_push(repo_full: str, branch: str) -> (bool, str):
    subprocess.run(["git", "add", "-A"], check=False)
    diff = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True).stdout
    if not diff:
        return True, ""
    msg = f"feat(auto): codex commit {_now()}"
    subprocess.run(["git", "commit", "-m", msg], check=False)
    if push_current(repo_full, branch):
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        return True, commit
    PATCHES.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "format-patch", "-1", "-o", str(PATCHES)], check=False)
    patches = sorted(PATCHES.glob("*.patch"), key=lambda p: p.stat().st_mtime)
    return False, patches[-1].name if patches else ""


def _update_baton(
    summary: str,
    next_suggestion: str,
    status: str,
    ref: str,
    ctx_bytes: int,
    pr_url: str | None = None,
    merge_decision: str | None = None,
) -> None:
    data = {
        "summary": redact(summary),
        "next_suggestion": redact(next_suggestion),
        "status": status,
        "context_bytes": ctx_bytes,
        "updated": _now(),
    }
    if status == "pushed":
        data["last_commit"] = ref
    else:
        data["last_patch"] = ref
    if pr_url:
        data["pr_url"] = pr_url
    if merge_decision:
        data["merge"] = merge_decision
    BATON_FILE.write_text(json.dumps(data, indent=2))


def run_taskcard(task_card: str, repo: str | None = None, branch: str | None = None) -> dict:
    """Execute a task card and update the baton.

    Returns a dict with summary, next_suggestion, status and commit_or_patch
    for direct consumption by the bridge.
    """
    prev_root = ctx.ROOT
    cwd = os.getcwd()
    remote_mode = ""
    pr_url = ""
    repo_cfg = CONFIG.get("repos", {}).get(repo or "", {})
    pr_mode = bool(int(os.getenv("PR_MODE", "0"))) or repo_cfg.get("pr_mode")
    base_branch = repo_cfg.get("branch", "main")
    target_branch = branch or base_branch
    if repo:
        workspace, _, remote_mode = ensure_workspace(repo, target_branch)
    else:
        workspace = ROOT
    try:
        ctx.ROOT = workspace
        os.chdir(workspace)
        envelope = _build_envelope(task_card, repo, target_branch)
        ctx_bytes = len(envelope.encode("utf-8"))
        result = _codex_call(envelope)
        try:
            validate_plan(result.files, repo)
        except ValueError as e:
            _update_baton(str(e), result.next_suggestion, "failed", "", ctx_bytes)
            return {
                "summary": str(e),
                "next_suggestion": result.next_suggestion,
                "status": "failed",
                "commit_or_patch": "",
                "remote_mode": remote_mode,
            }
        tests_ok = _run_commands(result.commands)
        _apply_files(result.files)
        pushed, ref = _try_push(repo or "", target_branch)
        status = "pushed" if pushed else "patched"
        merge_decision = None
        if pushed and repo and pr_mode:
            title = result.summary.splitlines()[0][:60]
            pr_url = ensure_pull_request(repo, target_branch, base_branch, title, result.summary)
            sha = ref
            state = "success" if tests_ok else "failure"
            set_commit_status(repo, sha, state, "codex/tests", "tests run")
            pr_number = pr_url.rstrip("/").split("/")[-1]
            ensure_labels(repo, pr_number, ["autofeature"])
            limits = get_limits(repo)
            if os.getenv("AUTOMERGE") == "1" and tests_ok and len(result.files) <= limits.get("max_files", 15):
                try:
                    enable_automerge(repo, pr_number)
                    merge_decision = "automerge"
                except Exception:
                    merge_decision = "manual"
            else:
                merge_decision = "manual"
        _update_baton(result.summary, result.next_suggestion, status, ref, ctx_bytes, pr_url or None, merge_decision)
    finally:
        os.chdir(cwd)
        ctx.ROOT = prev_root
    return {
        "summary": redact(result.summary),
        "next_suggestion": redact(result.next_suggestion),
        "status": status,
        "commit_or_patch": ref,
        "remote_mode": remote_mode,
        "pr_url": pr_url,
        "merge": merge_decision,
    }


async def run_taskcard_async(task_card: str, repo: str | None = None, branch: str | None = None) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, run_taskcard, task_card, repo, branch)


if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser()
    parser.add_argument("task_card", nargs="?")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--interval", type=int, default=60)
    args = parser.parse_args()

    if args.task_card:
        run_taskcard(args.task_card)
    elif args.watch:
        while True:
            time.sleep(args.interval)
    else:
        print("no task card provided")
