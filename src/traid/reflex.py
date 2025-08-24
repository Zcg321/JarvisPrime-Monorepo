"""Reflexive learning and memory handling for TrAId.
DNA:TRAID-REFLEX
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .model_stack import ModelStack

FAIL_FILE = Path("data/failed_trades.json")
FAIL_FILE.parent.mkdir(parents=True, exist_ok=True)
if not FAIL_FILE.exists():
    FAIL_FILE.write_text("{}")


class ReflexEngine:
    """Stores memory of trades and updates model weights."""

    def __init__(self, model_stack: ModelStack):
        self.model_stack = model_stack
        self.fail_memory: Dict[str, int] = json.loads(FAIL_FILE.read_text())
        self.trades: List[Dict] = []
        self.regret: Dict[str, float] = {}

    def record(self, trade: Dict) -> None:
        symbol = trade["symbol"]
        outcome = trade["profit"]
        scores = trade["scores"]
        if outcome < 0:
            self.fail_memory[symbol] = self.fail_memory.get(symbol, 0) + 1
            FAIL_FILE.write_text(json.dumps(self.fail_memory))
        self.model_stack.update(outcome, scores)
        self.trades.append(trade)
        if len(self.trades) > 100:
            self.trades.pop(0)

    def evaluate(self, real: Dict, ghost: Dict) -> None:
        delta = ghost["profit"] - real["profit"]
        for name, score in real["scores"].items():
            self.regret[name] = self.regret.get(name, 0.0) + delta * abs(score)
