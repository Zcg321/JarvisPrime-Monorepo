"""Run a one-day BTC/USD simulation using TrAId.
DNA:TRAID-RUNSIM
"""
from __future__ import annotations

from pprint import pprint

from .engine import TraidEngine
from .savepoint import load_state, save_state


def main() -> None:
    engine = TraidEngine()
    load_state(engine.model_stack, engine.reflex, engine.broker)
    result = engine.run_cycle("BTC-USD")
    save_state(engine.model_stack, engine.reflex, engine.broker)

    print("Final prediction:", result["executed"]["direction"])
    print("Confidence:", result["executed"]["confidence"])
    print("Real trade:")
    pprint(result["executed"])
    print("Ghost trade:")
    pprint(result["ghost"])
    print("Model scores:")
    pprint(engine.model_stack.get_scores())
    print("Reflex regret:")
    pprint(engine.reflex.regret)


if __name__ == "__main__":
    main()
