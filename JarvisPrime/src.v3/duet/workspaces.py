import os
import subprocess
from pathlib import Path
from contextlib import contextmanager
import asyncio
import threading
import yaml

LOCKS: dict[str, asyncio.Lock] = {}
PUSH_LOCKS: dict[str, threading.Lock] = {}

ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = ROOT / "workspaces"
CONFIG = yaml.safe_load((ROOT / "foreman/config.yaml").read_text())


def _token_for(owner: str, repo: str) -> str:
    env = f"GITHUB_TOKEN_{owner}__{repo}".upper().replace("-", "_")
    return os.getenv(env) or os.getenv("GT_TOKEN", "")


def ensure_workspace(repo_full: str, branch: str) -> tuple[Path, str, str]:
    if repo_full.startswith("/") or ".." in repo_full:
        raise ValueError("unsafe repo path")
    owner, name = repo_full.split("/", 1)
    WORKSPACES.mkdir(exist_ok=True)
    ws = WORKSPACES / f"{owner}__{name}"
    token = _token_for(owner, name)
    ssh_cmd = os.getenv("GIT_SSH_COMMAND")
    if token:
        url = f"https://x-access-token:{token}@github.com/{repo_full}.git"
        mode = "https"
    elif ssh_cmd:
        url = f"git@github.com:{repo_full}.git"
        mode = "ssh"
    else:
        url = f"https://github.com/{repo_full}.git"
        mode = "https"
    repo_cfg = CONFIG.get("repos", {}).get(repo_full, {})
    base_branch = repo_cfg.get("branch", "main")
    if not ws.exists():
        subprocess.run(["git", "clone", "--branch", base_branch, url, ws.as_posix()], check=True)
    else:
        subprocess.run(["git", "remote", "set-url", "origin", url], cwd=ws, check=False)
        subprocess.run(["git", "fetch"], cwd=ws, check=False)
    subprocess.run(["git", "checkout", base_branch], cwd=ws, check=False)
    if branch != base_branch:
        subprocess.run(["git", "checkout", "-B", branch, f"origin/{base_branch}"], cwd=ws, check=False)
    return ws, url, mode


async def acquire_lock(repo_full: str, branch: str) -> asyncio.Lock:
    key = f"{repo_full}:{branch}"
    lock = LOCKS.setdefault(key, asyncio.Lock())
    await lock.acquire()
    return lock


def release_lock(lock: asyncio.Lock) -> None:
    if lock.locked():
        lock.release()


@contextmanager
def with_repo_env(repo_full: str, branch: str):
    path, _, _ = ensure_workspace(repo_full, branch)
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(prev)


def push_current(repo_full: str, branch: str) -> bool:
    key = f"{repo_full}:{branch}"
    lock = PUSH_LOCKS.setdefault(key, threading.Lock())
    with lock:
        pr = subprocess.run(["git", "push", "origin", branch], capture_output=True)
    return pr.returncode == 0
