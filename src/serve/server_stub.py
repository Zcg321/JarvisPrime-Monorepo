"""Minimal HTTP stub for Jarvis Prime tools.

MIT License (c) 2025 Zack
"""
import json
import os
import re
import time
import math
import hashlib
import signal
import io
import csv
from collections import Counter
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Dict, Optional, Literal

from pydantic import BaseModel, ValidationError, Field

from src.core import anchors
from src.core.logio import append_jsonl_rotating
from src.reflex.core import Reflex
from src.core.errors import json_error
from src.serve import audit
from src.serve import logging as slog
from src.serve import policy
from src.serve import alerts, alerts_stream
from src.tools import (
    voice_mirror,
    savepoint,
    ghost,
    dfs,
    traid,
    surgecell,
    context_bridge,
    interaction,
    hardware_safety,
    plan,
    dfs_engine,
    dfs_roi_memory,
    dfs_exposure,
    dfs_portfolio,
    dfs_ghosts,
    ghost_dfs,
    dfs_showdown,
    bankroll_alloc,
    portfolio_eval,
)
from src.data import schedule
from src.tools import validate_inputs as validate_inputs_tool
from src.data import results as results_ingest
from src.savepoint import logger as savepoint_logger
from src.train import uptake
from src.serve import metrics
from src.serve import runtime_auto
from src.tools import submit_plan as submit_plan_tool
from src.config.loader import load_config
from src.serve import schemas, metrics_prom

# Allow experience log directory override via environment variable
uptake.LOG_DIR = Path(os.environ.get("JARVIS_EXP_DIR", "logs/experience"))

JSON_ONLY = re.compile(r'^\s*\{\s*"tool"\s*:\s*".+?"\s*,\s*"args"\s*:\s*\{.*\}\s*\}\s*$', re.S)
ANCHORS = anchors.load_all()
KILL = anchors.kill_phrase(ANCHORS['boot'])
REFLEX = Reflex()
START_TIME = time.time()
CFG_PATH = Path("configs/server.yaml")
try:
    CONFIG_SHA = hashlib.sha256(CFG_PATH.read_bytes()).hexdigest()
except Exception:
    CONFIG_SHA = ""
CFG = load_config().get("server", {})
PORT_CFG = CFG.get("port", 8000)
TOKENS = {t.get("token"): t for t in CFG.get("tokens", [])}
POLICIES = CFG.get("policies", [])
TOKEN_SET = set(TOKENS.keys())
REQUIRE_AUTH = CFG.get("require_auth", False)
RATE_CFG = CFG.get("rate", {})
RPS = RATE_CFG.get("rps", 1000)
BURST = RATE_CFG.get("burst", RPS)
RUNTIME = runtime_auto.init_runtime(os.environ.get("INFER_RUNTIME", "fp16"))
if RUNTIME == "int8":
    try:
        json.loads((Path("artifacts/quant/model_index.json")).read_text())
    except Exception:
        print("int8 runtime requested but missing quant artifacts; falling back to fp16", flush=True)
        RUNTIME = "fp16"
metrics.METRICS.quant_runtime = RUNTIME
RATE_STATE: dict = {}
COMPLIANCE_AUDIT_PATH = Path("logs/compliance/audit_trail/audit.jsonl")


def _parse_time(s: Optional[str]):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def _audit_query(token_id=None, tool=None, since=None, until=None):
    out = []
    for path in sorted(Path("logs/audit").glob("*.jsonl")):
        with path.open() as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                ts = _parse_time(rec.get("ts_iso"))
                if token_id and rec.get("token_id") != token_id:
                    continue
                if tool and rec.get("tool") != tool:
                    continue
                if since and ts and ts < since:
                    continue
                if until and ts and ts > until:
                    continue
                out.append(rec)
    return out


def _lineage_chain(lid: str):
    nodes = {}
    for sp in Path("logs/savepoints").glob("*.json"):
        try:
            data = json.loads(sp.read_text())
        except Exception:
            continue
        sid = data.get("lineage_id")
        if not sid:
            continue
        nodes[sid] = {"parent_id": data.get("parent_id"), "tool": data.get("event")}
    if lid not in nodes:
        return None
    ancestors = []
    pid = nodes[lid]["parent_id"]
    while pid and pid in nodes:
        ancestors.append({"lineage_id": pid, "tool": nodes[pid]["tool"]})
        pid = nodes[pid]["parent_id"]
    ancestors.reverse()
    descendants = [
        {"lineage_id": k, "tool": v["tool"]}
        for k, v in nodes.items()
        if v.get("parent_id") == lid
    ]
    descendants.sort(key=lambda x: x["lineage_id"])
    return {
        "lineage_id": lid,
        "tool": nodes[lid]["tool"],
        "ancestors": ancestors,
        "descendants": descendants,
    }


def _auth_token(headers) -> Optional[str]:
    auth = headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth.split(" ", 1)[1]


def _rate_key(token: Optional[str], client_ip: str) -> str:
    return token or client_ip


def _allow_rate(key: str) -> bool:
    now = time.time()
    tokens, last = RATE_STATE.get(key, (BURST, now))
    tokens = min(BURST, tokens + RPS * (now - last))
    if tokens < 1:
        RATE_STATE[key] = (tokens, now)
        metrics.METRICS.ratelimit_drops += 1
        return False
    RATE_STATE[key] = (tokens - 1, now)
    return True


def bad_request(reason: str, details: Optional[List[str]] = None):
    return json_error("BadRequest", 400, reason=reason, details=details)


class ResultsArgs(BaseModel):
    path: str
    ema_alpha: float = 0.35


class BankrollSlate(BaseModel):
    id: str
    type: Literal["classic", "showdown"]
    entries: int
    avg_entry_fee: float
    edge_hint: Optional[float] = None


class BankrollArgs(BaseModel):
    bankroll: float
    unit_fraction: Optional[float] = None
    slates: List[BankrollSlate]
    seed: int = 0


class PortfolioEvalArgs(BaseModel):
    lineups: List[dict]
    ownership_csv: str
    iters: int = 2000
    seed: int = 1337


class ScheduleArgs(BaseModel):
    start: str = Field(..., pattern=r"\d{4}-\d{2}-\d{2}")
    end: str = Field(..., pattern=r"\d{4}-\d{2}-\d{2}")
    type: Optional[Literal["classic", "showdown"]] = None


class ValidateInputsArgs(BaseModel):
    ownership_csv: str
    results_csv: Optional[str] = None
    lineups: List[dict]


class SubmitPlanArgs(BaseModel):
    slate_id: str
    lineups: List[dict]
    bankroll: float
    unit_fraction: Optional[float] = None
    entry_fee: float
    max_entries: int
    seed: Optional[int] = None


schemas.register("submit_plan", SubmitPlanArgs, {"type": "object"})

# Canonical tool names exposed via /chat {"message":"list_tools"}
CANONICAL_TO_FUNC = {}
CANONICAL_NAMES = [
    "dfs_pool",
    "dfs_exposure_solve",
    "dfs_portfolio",
    "dfs_record_result",
    "dfs_showdown",
    "dfs_calibrate",
    "slate_sim",
    "roi_report",
    "results_ingest",
    "bankroll_alloc",
    "portfolio_eval",
    "surgecell_apply",
    "voice_mirror_reflect",
    "dfs_lineup",
    "dfs_roi",
    "savepoint_write",
    "savepoint_list",
    "uptake_record",
    "uptake_replay",
    "uptake_search",
    "uptake_stats",
    "reflex_decide",
    "context_search",
    "plan_query",
    "surgecell",
    "voice_mirror",
    "savepoint",
    "dfs",
    "ghost_dfs.seed",
    "ghost_dfs.inject",
    "ghost_dfs",
    "traid_signal",
    "reflex",
    "schedule_query",
    "validate_inputs",
    "submit_plan",
    "chaos_harness",
]

# Describe available tools for discovery via legacy interfaces and /tools
TOOL_INFO = {
    "surgecell": "Return current resource allocation",
    "voice_mirror": "Reflect user text with clarity",
    "savepoint": "Persist a moment with optional metadata",
    "savepoint_list": "List recent savepoints",
    "dfs_roi": "Compute DFS ROI from entry results",
    "traid_signal": "Z-score over a price series",
    "ghost_dfs": "Monte Carlo DFS lineup simulation",
    "ghost_dfs.seed": "Deterministic ghost lineup seeding",
    "ghost_dfs.inject": "Mutate ghost lineup pool",
    "reflex": "Score proposals and self-check",
    "reflex_feedback": "Adjust Reflex source bias",
    "context_bridge": "Search mission anchors for a query",
    "dfs_predict": "Greedy DFS lineup generator",
    "dfs_pool": "Generate lineup pool with ghosts",
    "dfs_showdown": "Create showdown lineup with captain",
    "dfs_record_result": "Record DFS contest result",
    "dfs_exposure_solve": "Balance exposures across lineup pool",
    "dfs_portfolio": "Build multi-slate portfolio with exposure caps",
    "slate_sim": "Simulate ROI outcomes for a slate",
    "roi_report": "Generate ROI attribution report",
    "results_ingest": "Ingest contest results and update ROI",
    "bankroll_alloc": "Allocate bankroll tickets across slates",
    "portfolio_eval": "Estimate portfolio EV and risk",
    "schedule_query": "Query slate schedules",
    "validate_inputs": "Validate ownership, results, and lineup inputs",
    "dfs_calibrate": "Calibrate player projections",
    "hardware_safety": "Inspect GPU and recommend safe config",
    "web_fetch": "Fetch text from a URL (whitelisted)",
    "shell": "Execute a whitelisted shell command",
    "speak": "Simulated text-to-speech output",
    "listen": "Simulated speech-to-text input",
    "resurrect": "Reload anchors and kill phrase",
    "recall": "Return recent experiences",
    "replay": "Replay chronological experiences",
    "experience_search": "Search experience logs",
    "experience_stats": "Return count and last timestamp of experiences",
    "plan": "Generate action steps from anchors",
    "list_tools": "List available tools and descriptions",
}


def router(obj):
    global ANCHORS, KILL
    t = obj.get("tool")
    a = obj.get("args", {})
    if t == "surgecell":
        return {"allocation": surgecell.allocate(a.get("weights"))}
    if t == "voice_mirror":
        return {"reflection": voice_mirror.reflect(a.get("text", ""), a.get("affect", "calm"))}
    if t == "savepoint":
        path, lineage_id = savepoint_logger.savepoint_log(
            a.get("event", ""),
            a.get("payload", {}),
            a.get("affect"),
            a.get("bankroll"),
        )
        metrics.METRICS.savepoints_written += 1
        return {"path": str(path), "lineage_id": lineage_id}
    if t == "savepoint_list":
        return {"savepoints": savepoint.list_last(a.get("n", 5))}
    if t == "dfs_roi":
        return {"roi": dfs.roi(a.get("entries", []))}
    if t == "dfs_pool":
        return {"pool": dfs_engine.lineup_pool(a.get("players", []), a.get("budget", 0), a.get("n", 20), a.get("roster"), a.get("seed"))}
    if t == "dfs_showdown":
        metrics.METRICS.dfs_showdown_builds += 1
        return dfs_showdown.showdown_lineup(
            a.get("players", []),
            a.get("budget", 0),
            a.get("roi_bias"),
            stacks=a.get("stacks"),
            seed=a.get("seed", 0),
        )
    if t == "dfs_record_result":
        return dfs_engine.record_result(a.get("lineup", []), a.get("entry_fee", 0.0), a.get("winnings", 0.0))
    if t == "dfs_exposure_solve":
        return dfs_exposure.solve(
            a.get("slate_id", ""),
            a.get("n_lineups", 0),
            a.get("max_from_team", 3),
            a.get("global_exposure_caps"),
            a.get("seed", 0),
        )
    if t == "dfs_portfolio":
        return _dfs_portfolio(a)
    if t == "slate_sim":
        return _slate_sim(a)
    if t == "roi_report":
        return _roi_report(a)
    if t == "dfs_ghost_seed":
        return dfs_ghosts.seed(
            a.get("lineups_from", ""),
            a.get("k", 0),
            a.get("slate_id", ""),
            a.get("note"),
        )
    if t == "dfs_ghost_inject":
        return dfs_ghosts.inject(
            a.get("k", 0),
            a.get("mutate_rate", 0.0),
            a.get("salary_cap", 0.0),
            a.get("roster_slots"),
            a.get("max_from_team"),
            a.get("seed"),
        )
    if t == "dfs_calibrate":
        from src.tools.dfs_data_sources import mock_source
        players = a.get("players") or mock_source.fetch_players()
        res = dfs_engine.apply_calibration(
            players,
            a.get("alpha", 0.08),
            a.get("beta", 0.05),
            a.get("gamma", 0.04),
            a.get("seed"),
        )
        return {"players": res}
    if t == "traid_signal":
        return {"z": traid.zscore(a.get("price_series", []))}
    if t == "ghost_dfs":
        return ghost.dfs_sim(a.get("lineup", []), a.get("sims", 1000), a.get("seed"))
    if t == "reflex":
        decision = REFLEX.choose_action(a.get("proposals", []), a.get("affect", "calm"))
        check = REFLEX.self_check(decision)
        return {"decision": decision, "self_check": check}
    if t == "reflex_feedback":
        bias = REFLEX.feedback(a.get("source", ""), a.get("success", True))
        return {"bias": bias}
    if t == "context_bridge":
        return {"snippet": context_bridge.search(a.get("query", ""), ANCHORS)}
    if t == "dfs_predict":
        metrics.METRICS.dfs_builds += 1
        players = a.get("players", [])
        budget = a.get("budget", 0)
        roster = a.get("roster")
        return dfs.predict_lineup(players, budget, roster)
    if t == "hardware_safety":
        return {
            "info": hardware_safety.gpu_info(),
            "config": hardware_safety.recommend_config(a.get("min_gb", 24.0)),
        }
    if t == "web_fetch":
        return {"text": interaction.web_fetch(a.get("url", ""))}
    if t == "shell":
        try:
            return {"stdout": interaction.shell(a.get("cmd", ""))}
        except ValueError as exc:
            return {"error": str(exc)}
    if t == "speak":
        return {"said": interaction.speak(a.get("text", ""))}
    if t == "listen":
        return {"heard": interaction.listen(a.get("prompt"))}
    if t == "resurrect":
        try:
            ANCHORS = anchors.resurrect()
            KILL = anchors.kill_phrase(ANCHORS['boot'])
            return {"ok": True}
        except Exception:
            fallback = savepoint.list_last(1)
            return {"ok": False, "fallback": fallback[0] if fallback else None}
    if t == "recall":
        return {"experiences": uptake.list_last(a.get("n", 5))}
    if t == "replay":
        return {"experiences": uptake.replay(a.get("n"))}
    if t == "experience_search":
        return {"experiences": uptake.search(a.get("query", ""), a.get("n", 5))}
    if t == "experience_stats":
        return uptake.stats()
    if t == "plan":
        return {"steps": plan.generate(a.get("query", ""), ANCHORS)}
    if t == "list_tools":
        return {"tools": TOOL_INFO}
    return {"error": "unknown_tool", "tool": t}


def _dfs_roi(args):
    fees = args.get("entry_fees", [])
    winnings = args.get("winnings", [])
    total_fee = sum(fees)
    total_win = sum(winnings)
    net = total_win - total_fee
    roi_pct = (net / total_fee * 100) if total_fee else 0.0
    return {
        "total_fee": total_fee,
        "total_win": total_win,
        "net": net,
        "roi_pct": roi_pct,
    }


def _uptake_record(args):
    uptake.record(args.get("event", {}))
    return {"ok": True}


class _Slate(BaseModel):
    id: str
    type: Literal["classic", "showdown"]


class _PortfolioArgs(BaseModel):
    slates: List[_Slate]
    n_lineups: int
    max_from_team: int = 3
    global_exposure_caps: Optional[Dict[str, float]] = None
    scoring_mode: Literal["goku", "vegeta", "piccolo", "gohan"] = "gohan"
    seed: int = 0
    objectives: Optional[Dict[str, float]] = None
    as_plan: bool = False
    bankroll: Optional[float] = None
    unit_fraction: Optional[float] = None
    entry_fee: Optional[float] = None
    max_entries: Optional[int] = None


schemas.register("dfs_portfolio", _PortfolioArgs, {"type": "object"})


def _dfs_pool(args):
    from src.tools.dfs_data_sources import mock_source
    src = args.get("source", "mock")
    if src == "mock":
        players = mock_source.fetch_players()
    else:
        players = args.get("players", [])
    pool = dfs_engine.lineup_pool(
        players,
        args.get("salary_cap", 0),
        args.get("N", 20),
        args.get("roster_slots"),
        args.get("seed"),
    )
    return {"pool": pool[: args.get("N", 20)]}


def _dfs_exposure_solve(args):
    if "n_lineups" in args or "slate_id" in args:
        return dfs_exposure.solve(
            args.get("slate_id", ""),
            args.get("n_lineups", 0),
            args.get("max_from_team", 3),
            args.get("global_exposure_caps"),
            args.get("seed", 0),
        )
    from src.tools.dfs_data_sources import mock_source
    players = mock_source.fetch_players()
    pool = dfs_engine.lineup_pool(
        players,
        args.get("salary_cap", 0),
        args.get("target_size", 0),
        args.get("roster_slots"),
        args.get("seed"),
    )
    lineups = pool[: args.get("target_size", len(pool))]
    return {"lineups": lineups}


def _dfs_record_result(args):
    return dfs_roi_memory.record_result(
        [], args.get("entry_fee", 0.0), args.get("winnings", 0.0)
    )


def _dfs_showdown(args):
    metrics.METRICS.dfs_showdown_builds += 1
    return dfs_showdown.showdown_lineup(
        args.get("players", []),
        args.get("budget", 50000),
        args.get("roi_bias"),
        stacks=args.get("stacks"),
        seed=args.get("seed", 0),
    )


def _dfs_portfolio(args):
    parsed = _PortfolioArgs(**args)
    return dfs_portfolio.build(
        [s.model_dump() for s in parsed.slates],
        parsed.n_lineups,
        parsed.max_from_team,
        parsed.global_exposure_caps,
        parsed.scoring_mode,
        parsed.seed,
        parsed.objectives,
        parsed.as_plan,
        parsed.bankroll,
        parsed.unit_fraction,
        parsed.entry_fee,
        parsed.max_entries,
    )


def _slate_sim(args):
    from src.tools.slate_sim import run
    return run(
        args.get("lineups", []),
        args.get("ownership_csv", ""),
        args.get("iters", 1000),
        args.get("seed", 0),
    )


def _roi_report(args):
    from src.tools.roi_report import generate
    return generate(args.get("lookback_days", 60))


def _ghost_seed(args):
    return {
        "pool": ghost_dfs.seed_pool(
            args.get("slate_id", ""),
            args.get("seed", 0),
            args.get("pool_size", 50),
        )
    }


def _ghost_inject(args):
    return {
        "pool": ghost_dfs.mutate_pool(
            args.get("slate_id", ""),
            args.get("seed", 0),
            args.get("constraints"),
            args.get("cap", 50000),
        )
    }


def _results_ingest(args):
    a = ResultsArgs(**args)
    return results_ingest.ingest(a.path, a.ema_alpha)


def _bankroll_alloc(args):
    a = BankrollArgs(**args)
    return bankroll_alloc.allocate(a.bankroll, [s.dict() for s in a.slates], a.unit_fraction, a.seed)


def _portfolio_eval(args):
    a = PortfolioEvalArgs(**args)
    return portfolio_eval.evaluate(a.lineups, a.ownership_csv, a.iters, a.seed)


def _schedule_query(args):
    a = ScheduleArgs(**args)
    return schedule.query(a.start, a.end, a.type)


def _validate_inputs(args):
    a = ValidateInputsArgs(**args)
    return validate_inputs_tool.validate(a.ownership_csv, a.results_csv, a.lineups)


def _submit_plan(args):
    a = SubmitPlanArgs(**args)
    return submit_plan_tool.submit_plan(
        a.slate_id, a.lineups, a.bankroll, a.unit_fraction or 0.02, a.entry_fee, a.max_entries, a.seed or 0
    )


CANONICAL_TO_FUNC.update(
    {
        "dfs_pool": _dfs_pool,
        "dfs_exposure_solve": _dfs_exposure_solve,
        "dfs_portfolio": _dfs_portfolio,
        "dfs_record_result": _dfs_record_result,
        "dfs_showdown": _dfs_showdown,
        "ghost_dfs.seed": _ghost_seed,
        "ghost_dfs.inject": _ghost_inject,
        "dfs_calibrate": lambda a: router({"tool": "dfs_calibrate", "args": a}),
        "surgecell_apply": lambda a: router({"tool": "surgecell", "args": a}),
        "voice_mirror_reflect": lambda a: router({"tool": "voice_mirror", "args": a}),
        "dfs_lineup": lambda a: router({"tool": "dfs_predict", "args": a}),
        "dfs_roi": _dfs_roi,
        "savepoint_write": lambda a: router({"tool": "savepoint", "args": a}),
        "savepoint_list": lambda a: router({"tool": "savepoint_list", "args": a}),
        "uptake_record": _uptake_record,
        "uptake_replay": lambda a: router({"tool": "replay", "args": a}),
        "uptake_search": lambda a: router({"tool": "experience_search", "args": a}),
        "uptake_stats": lambda a: router({"tool": "experience_stats", "args": a}),
        "reflex_decide": lambda a: router({"tool": "reflex", "args": a}),
        "context_search": lambda a: router({"tool": "context_bridge", "args": a}),
        "plan_query": lambda a: router({"tool": "plan", "args": a}),
        "results_ingest": _results_ingest,
        "bankroll_alloc": _bankroll_alloc,
        "portfolio_eval": _portfolio_eval,
        "schedule_query": _schedule_query,
        "validate_inputs": _validate_inputs,
        "submit_plan": _submit_plan,
        "surgecell": lambda a: router({"tool": "surgecell", "args": a}),
        "voice_mirror": lambda a: router({"tool": "voice_mirror", "args": a}),
        "savepoint": lambda a: router({"tool": "savepoint", "args": a}),
        "dfs": lambda a: router({"tool": "dfs_predict", "args": a}),
        "ghost_dfs": lambda a: router({"tool": "ghost_dfs", "args": a}),
        "traid_signal": lambda a: router({"tool": "traid_signal", "args": a}),
        "reflex": lambda a: router({"tool": "reflex", "args": a}),
        "slate_sim": _slate_sim,
        "roi_report": _roi_report,
        "chaos_harness": lambda a: {"status": "ok"},
    }
)


def reply(user_text: str):
    if user_text.strip().lower() == KILL:
        resp = {"reply": "Acknowledged. Standing by."}
    elif user_text.strip().startswith("{"):
        if not JSON_ONLY.match(user_text):
            resp = {"error": "tool_json_format"}
        else:
            resp = {"tool_result": router(json.loads(user_text))}
    else:
        snippet = context_bridge.search(user_text, ANCHORS)
        if snippet:
            resp = {"reply": snippet}
        else:
            resp = {"reply": "I remember your mission. Tell me the smallest next true step, or send a JSON tool call."}
    try:
        uptake.record({"user": user_text, "response": resp})
    except Exception:
        pass
    return resp


class H(BaseHTTPRequestHandler):
    PORT = PORT_CFG
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
        return code

    def do_GET(self):
        start = time.time()
        token = _auth_token(self.headers)
        key = _rate_key(token, self.client_address[0])
        if self.path == "/health":
            alert_counts = alerts.counts_by_severity()
            code = self._send(
                200,
                {
                    "status": "ok",
                    "uptime_s": round(time.time() - START_TIME, 3),
                    "policy": REFLEX.policy,
                    "config_sha": CONFIG_SHA,
                    "tokens_configured": len(TOKENS),
                    "alerts_total": sum(alert_counts.values()),
                    "alerts_by_severity": alert_counts,
                    "audit_files": len(list(Path("logs/audit").glob("*.jsonl"))),
                    "savepoints_count": len(list(Path("logs/savepoints").glob("*.json"))),
                    "port": H.PORT,
                },
            )
        elif self.path == "/metrics":
            code = self._send(200, metrics.METRICS.snapshot())
        elif self.path == "/metrics/prom":
            if REQUIRE_AUTH and token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                data = metrics_prom.exposition()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(data.encode())
                code = 200
        elif self.path == "/alerts/stream":
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                for line in alerts_stream.stream_events():
                    try:
                        self.wfile.write(line.encode())
                        self.wfile.flush()
                    except Exception:
                        break
                code = 200
        elif self.path == "/list_tools_v2":
            if REQUIRE_AUTH and token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                code = self._send(200, schemas.list_tools())
        elif self.path == "/dashboard/json":
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                try:
                    data = Path("artifacts/reports/dashboard.json").read_text()
                    code = self._send(200, json.loads(data))
                except Exception:
                    code = self._send(404, {"error": "NotFound"})
        elif self.path.startswith("/alerts/summary"):
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                code = self._send(200, alerts.summary())
        elif self.path.startswith("/alerts"):
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                q = parse_qs(urlparse(self.path).query)
                sev = q.get("severity", [None])[0]
                since = _parse_time(q.get("since", [None])[0])
                code = self._send(200, alerts.get_last(since=since, severity=sev))
        elif self.path.startswith("/compliance/audit"):
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                entries = []
                if COMPLIANCE_AUDIT_PATH.exists():
                    with COMPLIANCE_AUDIT_PATH.open() as f:
                        for ln in f:
                            try:
                                entries.append(json.loads(ln))
                            except Exception:
                                continue
                code = self._send(200, entries[-50:])
        elif self.path.startswith("/audit/query"):
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                q = parse_qs(urlparse(self.path).query)
                fmt = q.get("format", ["json"])[0]
                recs = _audit_query(
                    token_id=q.get("token_id", [None])[0],
                    tool=q.get("tool", [None])[0],
                    since=_parse_time(q.get("since", [None])[0]),
                    until=_parse_time(q.get("until", [None])[0]),
                )
                if fmt == "summary":
                    summary = {
                        "per_tool": dict(Counter(r.get("tool") for r in recs)),
                        "per_token": dict(Counter(r.get("token_id") for r in recs)),
                        "total": len(recs),
                    }
                    code = self._send(200, summary)
                elif fmt == "csv":
                    buf = io.StringIO()
                    w = csv.writer(buf)
                    w.writerow(["ts", "tool", "token_id", "result_status"])
                    for r in recs:
                        w.writerow([r.get("ts_iso"), r.get("tool"), r.get("token_id"), r.get("result_status")])
                    data = buf.getvalue().encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    code = 200
                else:
                    code = self._send(200, recs)
        elif self.path.startswith("/lineage/"):
            if token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif TOKENS.get(token, {}).get("role") != "admin":
                code = self._send(403, {"error": "Forbidden"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                lineage_id = self.path.rsplit("/", 1)[1]
                chain = _lineage_chain(lineage_id)
                if chain:
                    code = self._send(200, chain)
                else:
                    code = self._send(404, {"error": "NotFound"})
        elif self.path == "/list_tools":
            if REQUIRE_AUTH and token not in TOKEN_SET:
                code = self._send(401, {"error": "Unauthorized"})
            elif not _allow_rate(key):
                code = self._send(429, {"error": "RateLimited"})
            else:
                code = self._send(200, {"tools": CANONICAL_NAMES})
        elif self.path == "/version":
            commit = os.environ.get("GIT_COMMIT")
            if not commit:
                commit = os.popen("git rev-parse --short HEAD 2>/dev/null").read().strip() or None
            code = self._send(
                200,
                {
                    "commit": commit,
                    "version": "nova-prime-v2",
                    "tools_count": len(CANONICAL_NAMES),
                },
            )
        elif self.path == "/tools":
            code = self._send(200, {"tools": TOOL_INFO})
        else:
            code = self._send(404, json_error("not_found", 404))
        append_jsonl_rotating("logs/server_access.jsonl", {
            "ts": time.time(),
            "path": self.path,
            "method": "GET",
            "status": code,
            "latency": round(time.time() - start, 6),
        })
        slog.log("info", f"GET {self.path} {code}", port=H.PORT)

    def do_POST(self):
        start = time.time()
        message_value = None
        token = _auth_token(self.headers)
        token_info = TOKENS.get(token)
        role = token_info.get("role") if token_info else None
        key = _rate_key(token, self.client_address[0])
        if self.path != "/chat":
            code = self._send(404, json_error("not_found", 404))
        elif REQUIRE_AUTH and token not in TOKEN_SET:
            code = self._send(401, {"error": "Unauthorized"})
        elif not _allow_rate(key):
            code = self._send(429, {"error": "RateLimited"})
        elif self.headers.get("Content-Type") != "application/json":
            code = self._send(415, json_error("unsupported_media_type", 415))
        else:
            ln = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(ln)
            try:
                body = raw.decode()
            except Exception:
                code = self._send(400, bad_request("invalid_json"))
            else:
                try:
                    data = json.loads(body or "{}")
                except Exception:
                    code = self._send(400, bad_request("invalid_json"))
                else:
                    if not isinstance(data, dict):
                        code = self._send(400, bad_request("invalid_request", ["root must be object"]))
                    else:
                        message_value = data.get("message")
                        args = data.get("args", {})
                        details = []
                        if not isinstance(message_value, str):
                            details.append("message must be string")
                        if not isinstance(args, dict):
                            details.append("args must be object")
                        def _finite(x):
                            if isinstance(x, float):
                                return math.isfinite(x)
                            if isinstance(x, dict):
                                return all(_finite(v) for v in x.values())
                            if isinstance(x, list):
                                return all(_finite(v) for v in x)
                            return True
                        if not _finite(args):
                            details.append("non-finite number")
                        if details:
                            code = self._send(400, bad_request("invalid_request", details))
                        elif message_value == KILL:
                            code = self._send(200, {"status": "standby"})
                        elif message_value == "list_tools":
                            code = self._send(200, {"tools": CANONICAL_NAMES})
                        elif not policy.allowed(role, message_value, POLICIES):
                            alerts.log_event("policy_deny", "role policy", role)
                            slog.alert("policy deny", component="policy", role=role)
                            code = self._send(403, {"error": "Forbidden", "reason": "role policy"})
                        elif message_value in CANONICAL_TO_FUNC:
                            try:
                                result = CANONICAL_TO_FUNC[message_value](args)
                                code = self._send(200, result)
                            except ValidationError as exc:
                                code = self._send(400, bad_request("invalid_args", exc.errors()))
                            except Exception as exc:
                                if slog.CURRENT_LEVEL <= slog.LEVELS["DEBUG"]:
                                    code = self._send(500, json_error("internal_error", 500, detail=str(exc)))
                                else:
                                    code = self._send(500, json_error("internal_error", 500))
                        else:
                            code = self._send(404, json_error("unknown_message", 404))
        duration = time.time() - start
        metrics.METRICS.record(duration * 1000, RUNTIME, code >= 400, role)
        append_jsonl_rotating(
            "logs/server_access.jsonl",
            {
                "ts": time.time(),
                "path": self.path,
                "method": "POST",
                "message": message_value,
                "status": code,
                "latency": round(duration, 6),
                "latency_ms": round(duration * 1000, 3),
                "runtime": RUNTIME,
            },
        )
        try:
            audit.record(message_value or "", args if isinstance(locals().get("args"), dict) else {}, token, token_info.get("id") if token_info else None, code)
        except Exception:
            pass
        lineage = result.get("lineage_id") if isinstance(locals().get("result"), dict) else None
        slog.log("info", f"POST {message_value} {code}", port=H.PORT, role=role, lineage_id=lineage)


def main() -> None:
    os.makedirs("logs/savepoints", exist_ok=True)
    port = int(os.environ.get("PORT", PORT_CFG))
    server = HTTPServer(("0.0.0.0", port), H)
    H.PORT = server.server_address[1]
    print(H.PORT, flush=True)

    def _shutdown(signum, frame):
        slog.log("info", "shutdown")
        server.shutdown()
        os._exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    slog.log("info", "startup", port=H.PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
