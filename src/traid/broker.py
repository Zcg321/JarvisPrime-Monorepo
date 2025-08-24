"""Simulated broker for trade execution.
DNA:TRAID-BROKER
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict

from .feeds import MarketState


class SimBroker:
    def __init__(self, balance: float = 10000.0) -> None:
        self.balance = balance
        self.position = 0.0
        self.trades: list[Dict] = []

    def execute(self, state: MarketState, signal: float, scores: Dict[str, float], tag: str,
                threshold: float = 0.2) -> Dict:
        direction = 0
        if signal > threshold:
            direction = 1
        elif signal < -threshold:
            direction = -1
        entry = state.prices[0] if state.prices else 0.0
        exit_ = state.prices[-1] if state.prices else 0.0
        profit = direction * (exit_ - entry)
        trade = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": state.symbol,
            "direction": direction,
            "entry": entry,
            "exit": exit_,
            "profit": float(profit),
            "scores": scores,
            "tag": tag,
        }
        self.trades.append(trade)
        return trade
