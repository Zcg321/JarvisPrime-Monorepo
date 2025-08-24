import time
from collections import deque
from pathlib import Path
from typing import Optional
import yaml
from src.serve import logging as slog
from src.serve import alerts

CONFIG = Path("configs/metrics.yaml")
try:
    _THRESHOLDS = yaml.safe_load(CONFIG.read_text()) or {}
except Exception:
    _THRESHOLDS = {}


class Metrics:
    def __init__(self) -> None:
        self.start = time.time()
        self.requests_total = 0
        self.requests_by_role = {}
        self.errors_total = 0
        self.lat_fp16 = deque(maxlen=1024)
        self.lat_int8 = deque(maxlen=1024)
        self.dfs_builds = 0
        self.dfs_showdown_builds = 0
        self.savepoints_written = 0
        self.quant_runtime = "fp16"
        self.alerts_total = 0
        self.alerts_file_size = 0
        self.alerts_rotations = 0
        self.thresholds = _THRESHOLDS
        self._breached = set()
        self.req_times = deque(maxlen=1024)
        slo = self.thresholds.get("slo", {})
        self.slo = slo
        self.error_budget_day = slo.get("error_budget_day", 0)
        self.error_budget_week = slo.get("error_budget_week", 0)
        self._budget_alerted = False
        self.day_start = self.week_start = time.time()
        self.ratelimit_drops = 0

    def record(self, latency_ms: float, runtime: str, error: bool, role: Optional[str] = None) -> None:
        self.requests_total += 1
        if role:
            self.requests_by_role[role] = self.requests_by_role.get(role, 0) + 1
        if error:
            self.errors_total += 1
        if runtime == "int8":
            self.lat_int8.append(latency_ms)
        else:
            self.lat_fp16.append(latency_ms)
        self.req_times.append(time.time())
        self._check_alerts()
        self._check_slo()

    def _avg(self, seq) -> float:
        return sum(seq) / len(seq) if seq else 0.0

    def _p95(self, seq) -> float:
        if not seq:
            return 0.0
        arr = sorted(seq)
        idx = max(int(0.95 * len(arr)) - 1, 0)
        return arr[idx]

    def snapshot(self) -> dict:
        avail = 1 - (self.errors_total / self.requests_total) if self.requests_total else 1.0
        slo = {
            "availability": round(avail, 4),
            "p95_targets": {
                "int8": self.slo.get("p95_latency_int8"),
                "fp16": self.slo.get("p95_latency_fp16"),
            },
            "error_budget": {
                "day": self.error_budget_day,
                "week": self.error_budget_week,
                "exhausted": self._budget_alerted,
            },
        }
        return {
            "uptime_s": round(time.time() - self.start, 3),
            "requests_total": self.requests_total,
            "errors_total": self.errors_total,
            "requests_total_by_role": self.requests_by_role,
            "avg_latency_ms_fp16": round(self._avg(self.lat_fp16), 3),
            "avg_latency_ms_int8": round(self._avg(self.lat_int8), 3),
            "dfs_builds": self.dfs_builds,
            "dfs_showdown_builds": self.dfs_showdown_builds,
            "savepoints_written": self.savepoints_written,
            "quant_runtime": self.quant_runtime,
            "alerts_total": self.alerts_total,
            "alerts_file_size": self.alerts_file_size,
            "alerts_rotations": self.alerts_rotations,
            "ratelimit_drops": self.ratelimit_drops,
            "thresholds": self.thresholds,
            "slo": slo,
        }

    def _check_alerts(self) -> None:
        now = time.time()
        while self.req_times and now - self.req_times[0] > 60:
            self.req_times.popleft()
        snap = {
            "avg_latency_ms_fp16": self._avg(self.lat_fp16),
            "avg_latency_ms_int8": self._avg(self.lat_int8),
            "error_rate": (self.errors_total / self.requests_total) if self.requests_total else 0.0,
            "requests_per_min": len(self.req_times),
        }
        for k, v in self.thresholds.items():
            if k == "slo":
                continue
            val = snap.get(k)
            if val is None:
                continue
            breached = val > v
            if breached and k not in self._breached:
                slog.alert(f"{k} {val:.3f} > {v}", component="metrics")
                alerts.log_event("slo_breach", f"{k} {val:.3f} > {v}")
                self.alerts_total += 1
                self._breached.add(k)
            elif not breached and k in self._breached:
                self._breached.remove(k)

    def _check_slo(self) -> None:
        now = time.time()
        if now - self.day_start > 86400:
            self.day_start = now
            self.error_budget_day = self.slo.get("error_budget_day", 0)
            self._budget_alerted = False
        if now - self.week_start > 604800:
            self.week_start = now
            self.error_budget_week = self.slo.get("error_budget_week", 0)
            self._budget_alerted = False
        avail_target = self.slo.get("availability", 0)
        int8_t = self.slo.get("p95_latency_int8", float("inf"))
        fp16_t = self.slo.get("p95_latency_fp16", float("inf"))
        avail = 1 - (self.errors_total / self.requests_total) if self.requests_total else 1.0
        breach = False
        if avail < avail_target:
            breach = True
        if self._p95(self.lat_int8) > int8_t:
            breach = True
        if self._p95(self.lat_fp16) > fp16_t:
            breach = True
        if breach:
            if self.error_budget_day > 0:
                self.error_budget_day -= 1
            if self.error_budget_week > 0:
                self.error_budget_week -= 1
            if not self._budget_alerted and (self.error_budget_day <= 0 or self.error_budget_week <= 0):
                slog.alert("error budget exhausted", component="metrics")
                alerts.log_event("slo_breach", "error budget exhausted")
                self.alerts_total += 1
                self._budget_alerted = True


METRICS = Metrics()
