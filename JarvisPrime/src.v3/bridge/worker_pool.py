import asyncio
import collections
import hashlib
import os
import json
import time
import uuid
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, Optional

from duet.duet_foreman import run_taskcard_async, BATON_FILE
from duet.workspaces import acquire_lock, release_lock
from .queue_store import QueueStore


@dataclass
class TaskItem:
    id: str
    task_card: str
    repo: Optional[str] = None
    branch: Optional[str] = None
    priority: int = 1
    hash: str = ""
    created_ts: float = time.time()
    attempts: int = 0


class WorkerPool:
    def __init__(self, config: dict):
        self.config = config
        pool_cfg = config.get("pool", {})
        self.max_workers = int(pool_cfg.get("max_workers", 3))
        self.max_per_repo = int(pool_cfg.get("max_per_repo", 1))
        self.queue_max = int(pool_cfg.get("queue_max", 200))
        rate_cfg = pool_cfg.get("rate_limits", {})
        self.openai_qps = int(rate_cfg.get("openai_qps", 3))
        self.openai_tpm = int(rate_cfg.get("openai_tpm", 80000))
        self.backoff_initial = int(rate_cfg.get("backoff_initial_ms", 1000)) / 1000
        self.backoff_max = int(rate_cfg.get("backoff_max_ms", 15000)) / 1000
        branch_cfg = config.get("branching", {})
        self.enable_isolation = branch_cfg.get("enable_isolation", False)
        self.branch_prefix = branch_cfg.get("branch_prefix", "autofeature/")

        self.queues: Dict[int, Deque[TaskItem]] = {
            0: collections.deque(),
            1: collections.deque(),
            2: collections.deque(),
        }
        self.pending_hash: Dict[str, TaskItem] = {}
        self.repo_counts: Dict[str, int] = collections.defaultdict(int)
        self.metrics = {
            "workers_busy": 0,
            "queue_depth": 0,
            "queue_depth_by_priority": {0: 0, 1: 0, 2: 0},
            "codex_calls_total": 0,
            "codex_429_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "dedupe_hits_total": 0,
        }
        self.workers: list[asyncio.Task] = []
        self.qps_tokens = self.openai_qps
        self.last_qps = time.monotonic()
        self.stop_event = asyncio.Event()
        self.max_retries = int(pool_cfg.get("max_retries", 3))
        self.shutdown_timeout = int(os.getenv("SHUTDOWN_TIMEOUT_SEC", pool_cfg.get("shutdown_timeout_sec", 10)))
        root = Path(__file__).resolve().parents[1] / "foreman"
        self.store = QueueStore(root)
        for rec in self.store.pending():
            item = TaskItem(
                id=rec["task_id"],
                task_card=rec["task_card"],
                repo=rec.get("repo"),
                branch=rec.get("branch"),
                priority=int(rec.get("priority", 1)),
                hash=rec.get("sha256", ""),
            )
            self.queues[item.priority].append(item)
            self.pending_hash[item.hash] = item
        self.metrics["queue_depth_by_priority"] = {k: len(v) for k, v in self.queues.items()}
        self.metrics["queue_depth"] = sum(len(q) for q in self.queues.values())

    def start(self):
        if self.workers:
            return
        for _ in range(self.max_workers):
            self.workers.append(asyncio.create_task(self._worker()))

    def stop(self):
        for w in self.workers:
            w.cancel()
        self.workers.clear()

    def _hash(self, task_card: str, repo: Optional[str], branch: Optional[str], priority: int) -> str:
        m = hashlib.sha256()
        m.update(task_card.encode())
        m.update(str(repo).encode())
        m.update(str(branch).encode())
        m.update(str(priority).encode())
        return m.hexdigest()

    def _position(self, priority: int) -> int:
        pos = 0
        for p in sorted(self.queues):
            q = self.queues[p]
            if p < priority:
                pos += len(q)
            elif p == priority:
                pos += len(q)
        return pos

    def enqueue(self, task_card: str, repo: Optional[str], branch: Optional[str], priority: int = 1):
        if self.stop_event.is_set():
            raise RuntimeError("pool shutting down")
        total = sum(len(q) for q in self.queues.values())
        if total >= self.queue_max:
            raise RuntimeError("queue full")
        h = self._hash(task_card, repo, branch, priority)
        if h in self.pending_hash:
            self.metrics["dedupe_hits_total"] += 1
            item = self.pending_hash[h]
            return item, False, self._position(item.priority)
        item = TaskItem(id=uuid.uuid4().hex[:8], task_card=task_card, repo=repo, branch=branch, priority=priority, hash=h, created_ts=time.time())
        self.queues[priority].append(item)
        self.pending_hash[h] = item
        self.metrics["queue_depth_by_priority"][priority] = len(self.queues[priority])
        self.metrics["queue_depth"] = sum(len(q) for q in self.queues.values())
        self.store.enqueue({"task_id": item.id, "task_card": task_card, "repo": repo, "branch": branch, "priority": priority, "sha256": h, "ts": item.created_ts})
        return item, True, self._position(priority)

    def cancel(self, task_id: str) -> bool:
        for q in self.queues.values():
            for i, item in enumerate(q):
                if item.id == task_id:
                    del q[i]
                    self.pending_hash.pop(item.hash, None)
                    self.metrics["queue_depth_by_priority"][item.priority] = len(q)
                    self.metrics["queue_depth"] = sum(len(x) for x in self.queues.values())
                    self.store.status(task_id, "cancelled")
                    return True
        return False

    async def _rate_limit(self):
        now = time.monotonic()
        elapsed = now - self.last_qps
        self.qps_tokens += elapsed * self.openai_qps
        if self.qps_tokens > self.openai_qps:
            self.qps_tokens = self.openai_qps
        self.last_qps = now
        while self.qps_tokens < 1:
            await asyncio.sleep(0.05)
            now = time.monotonic()
            elapsed = now - self.last_qps
            self.qps_tokens += elapsed * self.openai_qps
            self.last_qps = now
        self.qps_tokens -= 1

    async def _worker(self):
        while True:
            if self.stop_event.is_set() and all(len(q) == 0 for q in self.queues.values()):
                break
            item = None
            for p in sorted(self.queues):
                if self.queues[p]:
                    item = self.queues[p].popleft()
                    self.metrics["queue_depth_by_priority"][p] = len(self.queues[p])
                    break
            if not item:
                await asyncio.sleep(0.1)
                continue
            self.metrics["queue_depth"] = sum(len(q) for q in self.queues.values())
            self.pending_hash.pop(item.hash, None)
            repo_key = item.repo or "default"
            if self.repo_counts[repo_key] >= self.max_per_repo:
                self.queues[item.priority].append(item)
                await asyncio.sleep(0.1)
                continue
            self.repo_counts[repo_key] += 1
            self.metrics["workers_busy"] += 1
            try:
                await self._execute(item)
                self.metrics["tasks_completed"] += 1
                self.store.status(item.id, "completed")
            except Exception as e:
                item.attempts += 1
                if item.attempts < self.max_retries:
                    delay = min(self.backoff_initial * (2 ** (item.attempts - 1)), self.backoff_max)
                    await asyncio.sleep(delay + random.random())
                    self.queues[item.priority].append(item)
                    self.pending_hash[item.hash] = item
                    self.store.status(item.id, "retry", attempts=item.attempts)
                else:
                    self.metrics["tasks_failed"] += 1
                    err = str(e)
                    self.store.status(item.id, "failed", last_error=err)
                    self.store.move_to_dlq({
                        "task_id": item.id,
                        "task_card": item.task_card,
                        "repo": item.repo,
                        "branch": item.branch,
                        "priority": item.priority,
                        "last_error": err,
                    })
            finally:
                self.metrics["workers_busy"] -= 1
                self.repo_counts[repo_key] -= 1

    async def _execute(self, item: TaskItem):
        repo = item.repo
        branch = item.branch
        repo_cfg = self.config.get("repos", {}).get(repo or "", {})
        pr_mode = bool(int(os.getenv("PR_MODE", "0"))) or repo_cfg.get("pr_mode")
        base_branch = repo_cfg.get("branch", "main")
        if repo:
            if pr_mode:
                branch = f"{self.branch_prefix}{item.id}"
            elif not branch and self.enable_isolation and self.max_per_repo > 1:
                branch = f"{self.branch_prefix}{item.id}"
        lock = None
        if repo:
            lock = await acquire_lock(repo, branch or base_branch)
        backoff = self.backoff_initial
        while True:
            await self._rate_limit()
            try:
                result = await run_taskcard_async(item.task_card, repo=repo, branch=branch)
                if BATON_FILE.exists():
                    import json
                    baton = json.loads(BATON_FILE.read_text())
                else:
                    baton = {}
                baton.update({
                    "repo": repo,
                    "branch": branch or base_branch,
                    "remote_mode": result.get("remote_mode"),
                    "task_id": item.id,
                    "result": result.get("status"),
                })
                if result.get("pr_url"):
                    baton["pr_url"] = result["pr_url"]
                BATON_FILE.write_text(json.dumps(baton, indent=2))
                break
            except Exception as e:
                status = getattr(e, "status", None)
                self.metrics["codex_calls_total"] += 1
                if status == 429:
                    self.metrics["codex_429_total"] += 1
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, self.backoff_max)
                    continue
                raise
        if lock:
            release_lock(lock)

    async def shutdown(self):
        self.stop_event.set()
        start = time.monotonic()
        cancelled = 0
        while time.monotonic() - start < self.shutdown_timeout:
            if all(len(q) == 0 for q in self.queues.values()) and self.metrics["workers_busy"] == 0:
                break
            await asyncio.sleep(0.1)
        for q in self.queues.values():
            while q:
                item = q.popleft()
                cancelled += 1
                self.store.status(item.id, "cancelled")
        for w in self.workers:
            w.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        self.metrics["shutdown_ts"] = time.time()
        return cancelled
