import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class QueueStore:
    def __init__(self, root: Path, max_lines: int = 10000):
        self.queue_file = root / "queue.jsonl"
        self.dlq_file = root / "dlq.jsonl"
        self.max_lines = max_lines
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)
        self.queue_file.touch(exist_ok=True)
        self.dlq_file.touch(exist_ok=True)

    def _append(self, file: Path, record: Dict[str, Any]) -> None:
        with file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def enqueue(self, record: Dict[str, Any]) -> None:
        self._append(self.queue_file, {"type": "enqueue", **record})
        self._compact_if_needed(self.queue_file)

    def status(self, task_id: str, status: str, **extra: Any) -> None:
        self._append(self.queue_file, {"type": "status", "task_id": task_id, "status": status, **extra})
        self._compact_if_needed(self.queue_file)

    def move_to_dlq(self, record: Dict[str, Any]) -> None:
        self._append(self.dlq_file, record)
        self._compact_if_needed(self.dlq_file)

    def pending(self) -> List[Dict[str, Any]]:
        items: Dict[str, Dict[str, Any]] = {}
        for line in self.queue_file.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("type") == "enqueue":
                items[rec["task_id"]] = rec
            elif rec.get("type") == "status":
                if rec.get("status") in {"completed", "failed", "cancelled"}:
                    items.pop(rec["task_id"], None)
        return list(items.values())

    def dlq_summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for line in self.dlq_file.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            tid = rec.get("task_id")
            counts[tid] = counts.get(tid, 0) + 1
        return counts

    def requeue(self, task_id: str) -> Optional[Dict[str, Any]]:
        lines = self.dlq_file.read_text().splitlines()
        remain = []
        target = None
        for ln in lines:
            rec = json.loads(ln)
            if rec.get("task_id") == task_id and target is None:
                target = rec
            else:
                remain.append(ln)
        if target:
            self.dlq_file.write_text("\n".join(remain) + ("\n" if remain else ""))
            self.enqueue(target)
        return target

    def _compact_if_needed(self, file: Path) -> None:
        lines = file.read_text().splitlines()
        if len(lines) > self.max_lines:
            file.write_text("\n".join(lines[-self.max_lines:]) + "\n")
