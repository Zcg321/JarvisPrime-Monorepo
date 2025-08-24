"""Ghost trade simulator for TrAId.
DNA:TRAID-GHOST
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import numpy as np

from .reflex import ReflexEngine
from .feeds import MarketState

GHOST_FILE = Path("data/ghost_trades.json")
GHOST_FILE.parent.mkdir(parents=True, exist_ok=True)
if not GHOST_FILE.exists():
    GHOST_FILE.write_text("[]")


class GhostTrader:
    def __init__(self, reflex: ReflexEngine):
        self.reflex = reflex
        self.history = json.loads(GHOST_FILE.read_text())

    def run(self, state: MarketState, tag: str) -> Dict:
        ensemble, scores = self.reflex.model_stack.predict(state)
        prices = np.array(state.prices)
        direction = 1 if ensemble > 0 else -1
        profit = direction * (prices[-1] - prices[0])
        result = {
            "symbol": state.symbol,
            "direction": direction,
            "profit": float(profit),
            "scores": scores,
            "tag": tag,
            "ghost": True,
        }
        self.history.append(result)
        GHOST_FILE.write_text(json.dumps(self.history[-100:]))
        self.reflex.record(result)
        return result
