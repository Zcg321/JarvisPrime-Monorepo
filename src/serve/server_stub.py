"""Minimal HTTP stub for Jarvis Prime tools.

MIT License (c) 2025 Zack
"""
import json
import os
import re
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.core import anchors
from src.core.logio import append_jsonl_rotating
from src.reflex.core import Reflex
from src.core.errors import json_error
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
    dfs_ghosts,
)
from src.train import uptake

# Allow experience log directory override via environment variable
uptake.LOG_DIR = Path(os.environ.get("JARVIS_EXP_DIR", "logs/experience"))

JSON_ONLY = re.compile(r'^\s*\{\s*"tool"\s*:\s*".+?"\s*,\s*"args"\s*:\s*\{.*\}\s*\}\s*$', re.S)
ANCHORS = anchors.load_all()
KILL = anchors.kill_phrase(ANCHORS['boot'])
REFLEX = Reflex()
START_TIME = time.time()
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
RATE: dict = {}

# Canonical tool names exposed via /chat {"message":"list_tools"}
CANONICAL_TO_FUNC = {}
CANONICAL_NAMES = [
    "dfs_pool",
    "dfs_exposure_solve",
    "dfs_record_result",
    "dfs_showdown",
    "dfs_ghost_seed",
    "dfs_ghost_inject",
    "dfs_calibrate",
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
    "reflex": "Score proposals and self-check",
    "reflex_feedback": "Adjust Reflex source bias",
    "context_bridge": "Search mission anchors for a query",
    "dfs_predict": "Greedy DFS lineup generator",
    "dfs_pool": "Generate lineup pool with ghosts",
    "dfs_showdown": "Create showdown lineup with captain",
    "dfs_record_result": "Record DFS contest result",
    "dfs_exposure_solve": "Balance exposures across lineup pool",
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
        return {"reflection": voice_mirror.reflect(a.get("text", ""))}
    if t == "savepoint":
        return savepoint.save(a.get("moment", ""), a.get("meta"))
    if t == "savepoint_list":
        return {"savepoints": savepoint.list_last(a.get("n", 5))}
    if t == "dfs_roi":
        return {"roi": dfs.roi(a.get("entries", []))}
    if t == "dfs_pool":
        return {"pool": dfs_engine.lineup_pool(a.get("players", []), a.get("budget", 0), a.get("n", 20), a.get("roster"), a.get("seed"))}
    if t == "dfs_showdown":
        return dfs_engine.showdown_lineup(a.get("players", []), a.get("budget", 0), a.get("seed"))
    if t == "dfs_record_result":
        return dfs_engine.record_result(a.get("lineup", []), a.get("entry_fee", 0.0), a.get("winnings", 0.0))
    if t == "dfs_exposure_solve":
        return {"lineups": dfs_exposure.solve(a.get("pool", []), a.get("constraints", {}))}
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
    from src.tools.dfs_data_sources import mock_source
    players = mock_source.fetch_players()
    return dfs_engine.showdown_lineup(
        players, args.get("salary_cap", 0), args.get("seed")
    )


def _dfs_ghost_seed(args):
    return dfs_ghosts.seed(
        args.get("lineups_from", ""),
        args.get("k", 0),
        args.get("slate_id", ""),
        args.get("note"),
    )


def _dfs_ghost_inject(args):
    return dfs_ghosts.inject(
        args.get("k", 0),
        args.get("mutate_rate", 0.0),
        args.get("salary_cap", 0.0),
        args.get("roster_slots"),
        args.get("max_from_team"),
        args.get("seed"),
    )


CANONICAL_TO_FUNC.update(
    {
        "dfs_pool": _dfs_pool,
        "dfs_exposure_solve": _dfs_exposure_solve,
        "dfs_record_result": _dfs_record_result,
        "dfs_showdown": _dfs_showdown,
        "dfs_ghost_seed": _dfs_ghost_seed,
        "dfs_ghost_inject": _dfs_ghost_inject,
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
        if self.path == "/health":
            code = self._send(200, {"status": "ok", "uptime_s": round(time.time() - START_TIME, 3)})
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
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Jarvis Prime stub.")
            code = 200
        append_jsonl_rotating("logs/server_access.jsonl", {
            "ts": time.time(),
            "path": self.path,
            "method": "GET",
            "status": code,
            "latency": round(time.time() - start, 6),
        })

    def do_POST(self):
        start = time.time()
        message_value = None
        client = self.client_address[0]
        minute = int(time.time() // 60)
        RATE.setdefault((client, minute), 0)
        RATE[(client, minute)] += 1
        if RATE[(client, minute)] > 20:
            retry = 60 - (time.time() % 60)
            code = self._send(429, json_error("rate_limited", 429, retry_after_s=round(retry, 2)))
        elif self.path != "/chat":
            code = self._send(404, json_error("not_found", 404))
        else:
            if AUTH_TOKEN and self.headers.get("X-Auth-Token") != AUTH_TOKEN:
                code = self._send(401, json_error("unauthorized", 401))
            elif self.headers.get("Content-Type") != "application/json":
                code = self._send(415, json_error("unsupported_media_type", 415))
            else:
                ln = int(self.headers.get("Content-Length", "0") or "0")
                body = self.rfile.read(ln).decode() or "{}"
                try:
                    data = json.loads(body)
                except Exception:
                    code = self._send(400, json_error("invalid_json", 400))
                else:
                    message_value = data.get("message")
                    args = data.get("args", {})
                    details = []
                    if not isinstance(message_value, str):
                        details.append("message must be string")
                    if not isinstance(args, dict):
                        details.append("args must be object")
                    if details:
                        code = self._send(400, json_error("invalid_request", 400, details=details))
                    elif message_value == KILL:
                        code = self._send(200, {"status": "standby"})
                    elif message_value == "list_tools":
                        code = self._send(200, {"tools": CANONICAL_NAMES})
                    elif message_value in CANONICAL_TO_FUNC:
                        try:
                            result = CANONICAL_TO_FUNC[message_value](args)
                            code = self._send(200, result)
                        except Exception as exc:
                            code = self._send(500, json_error("internal_error", 500, detail=str(exc)))
                    else:
                        code = self._send(404, json_error("unknown_message", 404))
        append_jsonl_rotating(
            "logs/server_access.jsonl",
            {
                "ts": time.time(),
                "path": self.path,
                "method": "POST",
                "message": message_value,
                "status": code,
                "latency": round(time.time() - start, 6),
            },
        )


def main() -> None:
    os.makedirs("logs/savepoints", exist_ok=True)
    HTTPServer(("0.0.0.0", 8000), H).serve_forever()


if __name__ == "__main__":
    main()
