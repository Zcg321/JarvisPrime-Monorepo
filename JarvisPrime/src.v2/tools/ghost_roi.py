"""Daily ROI carryover store."""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any

import yaml

BASE = Path(os.environ.get("ROI_LOG_DIR_TOKENIZED", "logs/ghosts"))
LEGACY = Path(os.environ.get("ROI_LOG_DIR_LEGACY", "logs/ghosts"))


def _path(token_id: str | None) -> Path:
    return BASE / (token_id or "anon") / "roi_daily.jsonl"


LEGACY_PATH = LEGACY / "roi_daily.jsonl"
LEGACY_PATH.parent.mkdir(parents=True, exist_ok=True)


def record_daily_roi(entries: List[Dict[str, Any]], ts: float | None = None, token_id: str | None = None) -> None:
    ts = ts or time.time()
    date = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    path = _path(token_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for e in entries:
            rec = {"ts": ts, "date": date, **e}
            f.write(json.dumps(rec) + "\n")
    if os.environ.get("ROI_LOG_COMPAT_MIRROR") == "1":
        with LEGACY_PATH.open("a", encoding="utf-8") as f:
            for e in entries:
                rec = {"ts": ts, "date": date, **e}
                f.write(json.dumps(rec) + "\n")


def load_ema(player_id: str, slate_type: str, lookback_days: int = 90, alpha: float = 0.35, token_id: str | None = None) -> float:
    cfg_alpha = decay_alpha("nba", slate_type)
    if cfg_alpha is not None:
        alpha = cfg_alpha
    path = _path(token_id)
    if not path.exists():
        path = LEGACY_PATH
        if not path.exists():
            return 0.0
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    ema = None
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("player_id") != player_id or rec.get("slate_type") != slate_type:
                continue
            ts = datetime.fromtimestamp(rec.get("ts", 0), tz=timezone.utc)
            if ts < cutoff:
                continue
            roi = max(min(float(rec.get("roi", 0.0)), 0.35), -0.25)
            if ema is None:
                ema = roi
            else:
                ema = alpha * roi + (1 - alpha) * ema
    return 0.0 if ema is None else max(min(ema, 0.35), -0.25)


def half_life_to_alpha(days: float) -> float:
    return 1 - 0.5 ** (1 / days)


def decay_alpha(sport: str, slate_type: str) -> float | None:
    path = Path("configs/roi_decay.yaml")
    if not path.exists():
        return None
    cfg = yaml.safe_load(path.read_text()) or {}
    sport_cfg = cfg.get(sport.lower(), {})
    hl = sport_cfg.get(slate_type)
    if not hl:
        return None
    return half_life_to_alpha(float(hl))
