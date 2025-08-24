from typing import List, Dict, Any, Optional

from .dfs import (
    predict_lineup,
    _load_roi_ema,
    _load_roi_multi_ema,
)
from .dfs_scoring import adjust_projection
from .roi_cache import load_ema
from . import ghost_roi


def showdown_lineup(
    players: List[Dict[str, Any]],
    budget: float = 50000.0,
    roi_bias: Optional[Dict[str, Any]] = None,
    scoring_mode: str = "gohan",
    ownership: Optional[Dict[str, float]] = None,
    stacks: Optional[Dict[str, bool]] = None,
    seed: int = 0,
) -> Dict[str, Any]:
    """Build a DraftKings showdown lineup with simple CPT leverage."""

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

    adjusted: List[Dict[str, Any]] = []
    for p in players:
        name = p.get("name") or p.get("player")
        proj = float(p.get("proj", 0.0))
        if name in ema_multi:
            multi = ema_multi[name]
            val = multi.get("classic", 0.0) * 1.0 + multi.get("showdown", 0.0) * 1.15
            bias = max(min(val, 0.25), -0.15)
            proj *= 1 + bias
        elif name in ema:
            bias = max(min(ema[name], 0.25), -0.15)
            proj *= 1 + bias
        if roi_bias:
            carry = ghost_roi.load_ema(
                name,
                "showdown",
                int(roi_bias.get("lookback_days", 90)),
                float(roi_bias.get("alpha", 0.35)),
            )
            proj *= 1 + carry
        gap = float(p.get("ownership_gap", 0.0))
        corr = float(p.get("corr_util", 0.0))
        leverage_boost = 0.5 * gap + 0.5 * corr
        cpt_proj = proj * (1 + leverage_boost)
        own = None
        if ownership:
            own = float(ownership.get(name, 0.0)) / 100.0
        proj = adjust_projection(proj, own, scoring_mode)
        cpt_proj = adjust_projection(cpt_proj, own, scoring_mode)
        q = dict(p)
        q["proj"] = proj
        q["cpt_proj"] = cpt_proj
        adjusted.append(q)

    if not adjusted:
        return {"lineup": [], "cost": 0.0, "expected": 0.0, "remaining_budget": budget, "complete": False}

    cpt = sorted(
        adjusted,
        key=lambda x: (-x.get("cpt_proj", 0) / max(x.get("cost", 1), 1), str(x.get("name"))),
    )[0]
    remaining = [p for p in adjusted if p is not cpt]
    captain_team = cpt.get("team")
    if stacks and (stacks.get("captain_team") or stacks.get("bringback")):
        from .corr import bias_players
        bias_players(remaining, captain_team, bool(stacks.get("bringback")))
    cpt_cost = float(cpt.get("cost", 0)) * 1.5
    cpt_proj = float(cpt.get("cpt_proj", 0)) * 1.5
    util = predict_lineup(remaining, budget - cpt_cost, {"UTIL": 5}, None)
    if not util["lineup"]:
        util["lineup"] = sorted(remaining, key=lambda x: -x.get("proj", 0))[:5]
        util["cost"] = sum(float(p.get("cost", 0)) for p in util["lineup"])
        util["expected"] = sum(float(p.get("proj", 0)) for p in util["lineup"])
    lineup = [{**cpt, "slot": "CPT"}] + [{**p, "slot": p.get("slot", "UTIL")} for p in util["lineup"]]
    if stacks and stacks.get("captain_team"):
        from itertools import cycle
        same = [p for p in remaining if p.get("team") == captain_team]
        same_iter = cycle(sorted(same, key=lambda x: -x.get("proj", 0)) or [{}])
        new_lineup = [lineup[0]]
        for p in lineup[1:]:
            if p.get("team") != captain_team:
                try:
                    repl = next(same_iter)
                    new_lineup.append({**repl, "slot": "UTIL"})
                except StopIteration:
                    new_lineup.append(p)
            else:
                new_lineup.append(p)
        lineup = new_lineup
    if stacks and stacks.get("bringback"):
        if all(p.get("team") == captain_team for p in lineup[1:]):
            opps = [p for p in remaining if p.get("team") != captain_team]
            if opps:
                lineup[-1] = {**sorted(opps, key=lambda x: -x.get("proj", 0))[0], "slot": "UTIL"}
    total_cost = cpt_cost + util["cost"]
    expected = cpt_proj + util["expected"]
    remaining_budget = max(budget - total_cost, 0.0)
    complete = util["complete"] and len(lineup) == 6
    return {
        "lineup": lineup,
        "cost": total_cost,
        "expected": expected,
        "remaining_budget": remaining_budget,
        "complete": complete,
    }
