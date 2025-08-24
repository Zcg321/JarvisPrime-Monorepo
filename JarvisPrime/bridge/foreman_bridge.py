from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import yaml
import requests

from duet.duet_foreman import run_taskcard, run_taskcard_async, redact
from bridge.worker_pool import WorkerPool, TaskItem
from bridge.repo_infer import infer_repo_branch

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "foreman/config.yaml").read_text())
BATON_FILE = ROOT / "foreman" / "baton.json"
REQUESTS_FILE = ROOT / "foreman" / "requests.jsonl"
LOG_FILE = ROOT / "logs" / "bridge.jsonl"
ANCHORS = [
    ROOT / "core/jarvisprime/JarvisPrime_BootProtocol.md",
    ROOT / "core/jarvisprime/continuum_master_final.json",
    ROOT / "core/jarvisprime/continuum_ascension_path.json",
    ROOT / "core/jarvisprime/continuum_true_endgame.json",
]

app = FastAPI()

POOL = WorkerPool(CONFIG)

@app.on_event("startup")
async def _startup():
    POOL.start()

METRICS = POOL.metrics
METRICS.setdefault("idempotent_hits", 0)
METRICS.setdefault("auto_chain", 0)
METRICS.setdefault("planner_fallback", 0)
METRICS.setdefault("rate_limited", 0)

CHAIN_HISTORY: list[datetime] = []


def _load_requests():
    if REQUESTS_FILE.exists():
        lines = [l for l in REQUESTS_FILE.read_text().splitlines() if l.strip()]
        return [json.loads(l) for l in lines]
    return []


def _save_requests(entries):
    entries = entries[-200:]
    REQUESTS_FILE.write_text("\n".join(json.dumps(e) for e in entries))


def _log(route, status, key, rate_ok, summary, result):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "route": route,
        "status": status,
        "idempotency_key": key,
        "rate_limit_ok": rate_ok,
        "summary_preview": redact(summary)[:120] if summary else "",
        "result": result,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def _sign(body: str, token: str) -> str:
    return hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()


def _planner_call(baton: str) -> str:
    model = CONFIG.get("models", {}).get("queue")
    key = os.getenv("OPENAI_API_KEY")
    if not model or not key:
        return ""
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    prompt = (
        "Given the following baton excerpt, produce the next small Task Card."\
        " Keep it concise."
    )
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a planning assistant."},
            {"role": "user", "content": baton},
        ],
        "temperature": 0.2,
    }
    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return ""


def _chain_allowed() -> bool:
    auto_chain_max = int(os.getenv("AUTO_CHAIN_MAX", "5"))
    cooldown = int(os.getenv("AUTO_CHAIN_COOLDOWN_SEC", "90"))
    now = datetime.utcnow()
    while CHAIN_HISTORY and (now - CHAIN_HISTORY[0]).total_seconds() > 3600:
        CHAIN_HISTORY.pop(0)
    if len(CHAIN_HISTORY) >= auto_chain_max:
        return False
    if CHAIN_HISTORY and (now - CHAIN_HISTORY[-1]).total_seconds() < cooldown:
        return False
    CHAIN_HISTORY.append(now)
    return True


def _maybe_chain(result: dict) -> None:
    if os.getenv("AUTO_CHAIN", "0") != "1":
        return
    next_hint = result.get("next_suggestion", "").strip()
    if not next_hint:
        if os.getenv("PLANNER_FALLBACK", "1") == "1":
            baton = BATON_FILE.read_text() if BATON_FILE.exists() else ""
            next_hint = _planner_call(baton)
            if not next_hint:
                return
            METRICS["planner_fallback"] += 1
        else:
            return
    length = len(next_hint)
    if length < 20 or length > 480 or "rewrite repo" in next_hint.lower() or "large refactor" in next_hint.lower():
        if os.getenv("PLANNER_FALLBACK", "1") == "1":
            baton = BATON_FILE.read_text() if BATON_FILE.exists() else ""
            next_hint = _planner_call(baton)
            if not next_hint:
                return
            METRICS["planner_fallback"] += 1
        else:
            return
    if not _chain_allowed():
        return
    body = json.dumps({"task_card": next_hint})
    token = os.getenv("FOREMAN_SHARED_TOKEN", "")
    if not token:
        return
    headers = {
        "Content-Type": "application/json",
        "X-Foreman-Id": CONFIG.get("foreman_id"),
        "X-Foreman-Conv": CONFIG.get("conversation_hint"),
        "X-Foreman-Sign": _sign(body, token),
        "X-Idempotency-Key": hashlib.sha256(next_hint.encode()).hexdigest()[:16],
    }
    try:
        requests.post("http://localhost:8787/v1/taskcards", data=body, headers=headers, timeout=10)
        METRICS["auto_chain"] += 1
        _log("auto_chain", 200, headers.get("X-Idempotency-Key"), True, next_hint, "chained")
    except Exception:
        _log("auto_chain", 500, headers.get("X-Idempotency-Key"), True, next_hint, "failed")


def _verify(req: Request, body: bytes) -> None:
    token = os.getenv("FOREMAN_SHARED_TOKEN")
    if not token:
        raise HTTPException(status_code=401, detail="missing FOREMAN_SHARED_TOKEN")
    fid = req.headers.get("X-Foreman-Id")
    conv = req.headers.get("X-Foreman-Conv")
    sign = req.headers.get("X-Foreman-Sign")
    if fid != CONFIG.get("foreman_id") or conv != CONFIG.get("conversation_hint"):
        raise HTTPException(status_code=403, detail="invalid foreman headers")
    expected = hmac.new(token.encode(), body, hashlib.sha256).hexdigest()
    if not sign or not hmac.compare_digest(sign, expected):
        raise HTTPException(status_code=403, detail="signature mismatch")


@app.post("/v1/taskcards")
async def post_taskcards(req: Request):
    body = await req.body()
    _verify(req, body)
    data = await req.json()
    task = data.get("task_card", "")
    repo = data.get("repo")
    branch = data.get("branch")
    policy_key = data.get("policy_key")
    priority_name = data.get("priority", "normal")
    priority_map = {"high": 0, "normal": 1, "low": 2}
    priority = priority_map.get(priority_name, 1)
    inference_reason = None
    if not repo and policy_key:
        policy = CONFIG.get("routing", {}).get("policies", {}).get(policy_key)
        if policy:
            repo = policy.get("repo")
            branch = policy.get("branch")
    if not repo:
        policies = CONFIG.get("routing", {}).get("policies", {})
        default = CONFIG.get("routing", {}).get("default", {})
        repo, branch, inference_reason = infer_repo_branch(task, policies, default)
    key = req.headers.get("X-Idempotency-Key")

    entries = _load_requests()
    now = datetime.utcnow()

    # idempotency check
    if key:
        for e in reversed(entries):
            if e.get("key") == key and e.get("response"):
                if now - datetime.fromisoformat(e["ts"]) < timedelta(minutes=10):
                    METRICS["idempotent_hits"] += 1
                    resp = e["response"]
                    _log("/v1/taskcards", 200, key, True, resp.get("summary", ""), resp.get("status"))
                    return resp
                break

    # rate limit
    recent = [e for e in entries if e.get("processed") and now - datetime.fromisoformat(e["ts"]) < timedelta(seconds=60)]
    if len(recent) >= 6:
        METRICS["rate_limited"] += 1
        _log("/v1/taskcards", 429, key, False, "", "rate_limited")
        raise HTTPException(status_code=429, detail="rate limit exceeded", headers={"Retry-After": "10"})

    total_depth = sum(len(q) for q in POOL.queues.values())
    if req.query_params.get("sync") == "1" and total_depth == 0 and METRICS["workers_busy"] == 0:
        try:
            result = run_taskcard(task, repo=repo, branch=branch or "main")
        except Exception:
            METRICS["tasks_failed"] += 1
            raise HTTPException(status_code=500, detail="executor error")
        METRICS["tasks_completed"] += 1
        resp = {"accepted": True, "task_id": now.strftime("%Y%m%d%H%M%S%f"), **result, "repo": repo, "branch": branch or "main"}
        if BATON_FILE.exists():
            baton = json.loads(BATON_FILE.read_text())
        else:
            baton = {}
        baton.update({
            "repo": repo,
            "branch": branch or "main",
            "remote_mode": result.get("remote_mode"),
            "task_id": resp["task_id"],
            "result": result["status"],
        })
        BATON_FILE.write_text(json.dumps(baton, indent=2))
        entries.append({"ts": now.isoformat(), "key": key, "response": resp, "processed": True})
        _save_requests(entries)
        _log("/v1/taskcards", 200, key, True, result.get("summary", ""), result.get("status"))
        _maybe_chain(result)
        return resp

    item, accepted, pos = POOL.enqueue(task, repo, branch, priority)
    if not accepted:
        _log("/v1/taskcards", 200, key, True, "", "deduped")
        return {"accepted": False, "duplicated_of": item.id}
    entries.append({"ts": now.isoformat(), "key": key, "task_id": item.id, "processed": False})
    _save_requests(entries)
    METRICS["queue_depth"] = sum(len(q) for q in POOL.queues.values())
    _log("/v1/taskcards", 202, key, True, task[:100], "enqueued")
    resp = {
        "accepted": True,
        "task_id": item.id,
        "position": pos,
        "priority": priority_name,
        "repo": repo,
        "branch": branch or "main",
    }
    if inference_reason:
        resp["inference_reason"] = inference_reason
    return resp


@app.get("/v1/queue")
def get_queue():
    total = sum(len(q) for q in POOL.queues.values())
    return {
        "queue_depth": total,
        "workers_busy": METRICS["workers_busy"],
        "per_repo_inflight": dict(POOL.repo_counts),
        "queue_depth_by_priority": {k: len(v) for k, v in POOL.queues.items()},
    }


@app.post("/v1/taskcards/cancel")
async def cancel_task(req: Request):
    body = await req.body()
    _verify(req, body)
    data = await req.json()
    tid = data.get("task_id")
    ok = POOL.cancel(tid)
    if not ok:
        raise HTTPException(status_code=404, detail="task not found")
    return {"cancelled": True}


@app.get("/v1/dlq")
def get_dlq():
    return POOL.store.dlq_summary()


@app.post("/v1/dlq/requeue")
async def dlq_requeue(req: Request):
    body = await req.body()
    _verify(req, body)
    data = await req.json()
    tid = data.get("task_id")
    rec = POOL.store.requeue(tid)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    POOL.enqueue(rec["task_card"], rec.get("repo"), rec.get("branch"), int(rec.get("priority", 1)))
    return {"requeued": True}


@app.get("/v1/baton")
def get_baton():
    if BATON_FILE.exists():
        return json.loads(BATON_FILE.read_text())
    return {}


@app.get("/v1/health")
def get_health():
    branch = subprocess.run([
        "git",
        "rev-parse",
        "--abbrev-ref",
        "HEAD",
    ], capture_output=True, text=True).stdout.strip()
    anchors_present = [p.name for p in ANCHORS if p.exists()]
    baton = {}
    if BATON_FILE.exists():
        baton = json.loads(BATON_FILE.read_text())
    return {
        "ok": True,
        "git_branch": branch,
        "anchors_present": anchors_present,
        "last_push_status": baton.get("status"),
    }


@app.get("/v1/metrics")
def get_metrics():
    return {"metrics": METRICS}


@app.post("/v1/admin/shutdown")
async def admin_shutdown(req: Request):
    body = await req.body()
    _verify(req, body)
    cancelled = await POOL.shutdown()
    return {"stopped": True, "cancelled": cancelled, "drained": METRICS["tasks_completed"]}
