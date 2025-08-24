import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src.data import schedule
from src.tools import portfolio_eval, bankroll_alloc


def main():
    slates = schedule.query("2025-10-25", "2025-10-25")
    stats = portfolio_eval.evaluate([], "data/ownership/sample_classic.csv", iters=10, seed=1)
    plan = bankroll_alloc.allocate(10.0, [{"id": s["slate_id"], "type": s["type"], "entries":1, "avg_entry_fee":1.0} for s in slates], 0.01, 1)
    summary = {"slates": len(slates), "ev": stats["ev"], "plan_size": len(plan.get("allocations", []))}
    print(json.dumps(summary))

if __name__ == "__main__":
    main()
