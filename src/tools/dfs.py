from typing import List, Dict, Any, Optional

def roi(entries: List[Dict[str, float]]) -> float:
    """Compute ROI given entries of profit and cost."""
    profit = sum(e.get('profit', 0.0) for e in entries)
    cost = sum(e.get('cost', 0.0) for e in entries)
    return (profit - cost) / cost if cost else 0.0


def predict_lineup(
    players: List[Dict[str, Any]],
    budget: float,
    roster: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Greedy lineup selection under a budget and roster schema.

    Parameters
    ----------
    players: list of dicts with ``name``, ``pos``, ``cost`` and ``proj``
    budget: total salary cap
    roster: position slots, defaults to DraftKings NFL classic

    Returns
    -------
    dict with lineup, total cost and expected projection
    """
    if roster is None:
        roster = {"QB": 1, "RB": 2, "WR": 3, "FLEX": 1}

    slots = roster.copy()
    lineup: List[Dict[str, Any]] = []
    names = set()
    total_cost = 0.0
    expected = 0.0

    players_sorted = sorted(
        players,
        key=lambda x: x.get("proj", 0) / max(x.get("cost", 1), 1),
        reverse=True,
    )

    # Fill fixed positions first
    for pos, count in list(slots.items()):
        if pos == "FLEX":
            continue
        for p in [pl for pl in players_sorted if pl.get("pos") == pos and pl.get("name") not in names]:
            if count <= 0:
                break
            cost = float(p.get("cost", 0))
            if total_cost + cost > budget:
                continue
            lineup.append(p)
            names.add(p.get("name"))
            total_cost += cost
            expected += float(p.get("proj", 0))
            count -= 1
        slots[pos] = count

    # Fill FLEX positions from remaining RB/WR/TE
    flex_slots = slots.get("FLEX", 0)
    if flex_slots:
        flex_positions = {"RB", "WR", "TE"}
        for p in [pl for pl in players_sorted if pl.get("name") not in names and pl.get("pos") in flex_positions]:
            if flex_slots <= 0:
                break
            cost = float(p.get("cost", 0))
            if total_cost + cost > budget:
                continue
            lineup.append(p)
            names.add(p.get("name"))
            total_cost += cost
            expected += float(p.get("proj", 0))
            flex_slots -= 1
    slots["FLEX"] = flex_slots

    remaining_slots = {k: v for k, v in slots.items() if k != "FLEX" and v > 0}
    if flex_slots := slots.get("FLEX", 0):
        remaining_slots["FLEX"] = flex_slots
    complete = sum(remaining_slots.values()) == 0
    return {
        "lineup": lineup,
        "cost": total_cost,
        "expected": expected,
        "remaining_budget": max(budget - total_cost, 0.0),
        "complete": complete,
    }
