import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from src.tools.dfs_scoring import adjust_projection
from src.tools.roi_cache import load_ema
from . import ghost_roi

from src.savepoint.logger import savepoint_log

ROI_LOG = Path("logs/ghosts/roi.jsonl")


def _load_roi_ema(lookback_days: int, alpha: float) -> Dict[str, float]:
    """Compute per-player ROI exponential moving average."""

    ema: Dict[str, float] = {}
    if not ROI_LOG.exists():
        return ema
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)
    try:
        lines = ROI_LOG.read_text().splitlines()
    except Exception:
        return ema
    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        ts = rec.get("ts") or rec.get("ts_iso")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
            except Exception:
                pass
        name = rec.get("player") or rec.get("player_id") or rec.get("name")
        if not name:
            continue
        roi_val = rec.get("roi")
        if roi_val is None:
            profit = rec.get("profit")
            cost = rec.get("cost")
            if cost:
                roi_val = (profit - cost) / cost
            else:
                continue
        prev = ema.get(name, 0.0)
        ema[name] = alpha * float(roi_val) + (1 - alpha) * prev
    return ema


def _load_roi_multi_ema(decay_days: int, alpha: float) -> Dict[str, Dict[str, float]]:
    """EMA of ROI grouped by player and slate type."""

    ema: Dict[str, Dict[str, float]] = {}
    if not ROI_LOG.exists():
        return ema
    cutoff = datetime.utcnow() - timedelta(days=decay_days)
    try:
        lines = ROI_LOG.read_text().splitlines()
    except Exception:
        return ema
    for line in lines:
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        ts = rec.get("ts") or rec.get("ts_iso")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
            except Exception:
                pass
        name = rec.get("player") or rec.get("player_id") or rec.get("name")
        if not name:
            continue
        slate_type = str(rec.get("slate_type") or "classic").lower()
        slate_key = "showdown" if slate_type.startswith("show") else "classic"
        roi_val = rec.get("roi")
        if roi_val is None:
            profit = rec.get("profit")
            cost = rec.get("cost")
            if cost:
                roi_val = (profit - cost) / cost
            else:
                continue
        player_rec = ema.setdefault(name, {"classic": 0.0, "showdown": 0.0})
        prev = player_rec.get(slate_key, 0.0)
        player_rec[slate_key] = alpha * float(roi_val) + (1 - alpha) * prev
    return ema


def roi(entries: List[Dict[str, float]]) -> float:
    """Compute ROI given entries of profit and cost."""

    profit = sum(e.get("profit", 0.0) for e in entries)
    cost = sum(e.get("cost", 0.0) for e in entries)
    return (profit - cost) / cost if cost else 0.0


# Position groups for flexible roster slots
GROUPS: Dict[str, Set[str]] = {
    "FLEX": {"RB", "WR", "TE"},
    "G": {"PG", "SG"},
    "F": {"SF", "PF"},
    "UTIL": {"QB", "RB", "WR", "TE", "PG", "SG", "SF", "PF", "C"},
    "CPT": {"QB", "RB", "WR", "TE", "PG", "SG", "SF", "PF", "C"},
}


def _assign_player(
    player: Dict[str, Any],
    slot: str,
    slots: Dict[str, int],
    names: Set[str],
    budget: float,
    total_cost: float,
    expected: float,
) -> Optional[Dict[str, float]]:
    """Attempt to assign ``player`` to ``slot`` respecting budget.

    Returns updated cost/expected if successful, otherwise ``None``.
    """

    if slots.get(slot, 0) <= 0 or player.get("name") in names:
        return None

    cost = float(player.get("cost", 0))
    proj = float(player.get("proj", 0))
    if slot == "CPT":
        cost *= 1.5
        proj *= 1.5

    if total_cost + cost > budget:
        return None

    slots[slot] -= 1
    names.add(player.get("name", ""))
    return {"cost": cost, "proj": proj}


def predict_lineup(
    players: List[Dict[str, Any]],
    budget: float,
    roster: Optional[Dict[str, int]] = None,
    roi_bias: Optional[Dict[str, Any]] = None,
    scoring_mode: str = "gohan",
    ownership: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Greedy lineup selection under a budget and roster schema.

    Supports DraftKings style rosters including NBA (``PG/SG/SF/PF/C/G/F/UTIL``)
    and showdown (``CPT/UTIL``) in addition to the NFL classic default.
    Players may list multiple positions separated by ``/`` (e.g. ``"PG/SG"``).
    ``remaining_budget`` reports unused salary.
    """

    if roster is None:
        roster = {"QB": 1, "RB": 2, "WR": 3, "FLEX": 1}

    slots = roster.copy()
    lineup: List[Dict[str, Any]] = []
    names: Set[str] = set()
    total_cost = 0.0
    expected = 0.0

    ema: Dict[str, float] = {}
    ema_multi: Dict[str, Dict[str, float]] = {}
    if roi_bias:
        ms = roi_bias.get("multi_slate") if isinstance(roi_bias.get("multi_slate"), dict) else None
        if ms and ms.get("enabled"):
            ema_multi = load_ema(
                int(ms.get("decay_days", 45)),
                float(ms.get("alpha", 0.35)),
                multi=True,
            )
        else:
            ema = load_ema(
                int(roi_bias.get("lookback_days", 30)),
                float(roi_bias.get("alpha", 0.35)),
            )
    adjusted_players: List[Dict[str, Any]] = []
    for p in players:
        name = p.get("name") or p.get("player")
        adj = p.get("proj", 0.0)
        if name in ema_multi:
            multi = ema_multi[name]
            val = multi.get("classic", 0.0) * 1.0 + multi.get("showdown", 0.0) * 1.15
            bias = max(min(val, 0.25), -0.15)
            adj *= 1 + bias
        elif name in ema:
            bias = max(min(ema[name], 0.25), -0.15)
            adj *= 1 + bias
        if roi_bias:
            carry = ghost_roi.load_ema(
                name,
                "classic",
                int(roi_bias.get("lookback_days", 90)),
                float(roi_bias.get("alpha", 0.35)),
            )
            adj *= 1 + carry
        own = None
        if ownership:
            own = float(ownership.get(name, 0.0)) / 100.0
        q = dict(p)
        q["proj"] = adjust_projection(adj, own, scoring_mode)
        adjusted_players.append(q)

    players_sorted = sorted(
        adjusted_players,
        key=lambda x: (
            -x.get("proj", 0) / max(x.get("cost", 1), 1),
            str(x.get("name")),
        ),
    )

    # Fill strict positions first (those not defined in GROUPS)
    for pos in [p for p in slots if p not in GROUPS]:
        count = slots.get(pos, 0)
        for player in players_sorted:
            if count <= 0:
                break
            pos_list = set(str(player.get("pos", "")).split("/"))
            if pos not in pos_list:
                continue
            res = _assign_player(player, pos, slots, names, budget, total_cost, expected)
            if res:
                lineup.append({**player, "slot": pos})
                total_cost += res["cost"]
                expected += res["proj"]
                count -= 1
        slots[pos] = count

    # Fill flexible/group slots in priority order
    for slot in ["CPT", "FLEX", "G", "F", "UTIL"]:
        count = slots.get(slot, 0)
        if count <= 0:
            continue
        allowed = GROUPS.get(slot, set())
        for player in players_sorted:
            if count <= 0:
                break
            if player.get("name") in names:
                continue
            pos_list = set(str(player.get("pos", "")).split("/"))
            if not (pos_list & allowed):
                continue
            res = _assign_player(player, slot, slots, names, budget, total_cost, expected)
            if res:
                lineup.append({**player, "slot": slot})
                total_cost += res["cost"]
                expected += res["proj"]
                count -= 1
        slots[slot] = count

    remaining_slots = {k: v for k, v in slots.items() if v > 0}
    complete = sum(remaining_slots.values()) == 0
    result = {
        "lineup": lineup,
        "cost": total_cost,
        "expected": expected,
        "remaining_budget": max(budget - total_cost, 0.0),
        "complete": complete,
    }
    try:
        savepoint_log("dfs_lineup", result, None, None)
    except Exception:
        pass
    return result
