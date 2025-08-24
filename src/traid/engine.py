"""TraidEngine orchestrates feeds, models, reflexive learning and trade execution.
DNA:TRAID-ENGINE
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import Dict


from .feeds import Feeds, MarketState
from .model_stack import ModelStack
from .reflex import ReflexEngine
from .ghost import GhostTrader
from .broker import SimBroker


class TraidEngine:
    def __init__(self, broker: SimBroker | None = None) -> None:
        self.feeds = Feeds()
        self.model_stack = ModelStack()
        self.reflex = ReflexEngine(self.model_stack)
        self.ghost = GhostTrader(self.reflex)
        self.broker = broker or SimBroker()
        self.parent_tag = "root"

    def _dna(self) -> str:
        tag = f"DNA:{uuid4().hex}|{datetime.utcnow().isoformat()}|{self.parent_tag}"
        self.parent_tag = tag
        return tag

    def prepare_state(self, symbol: str) -> MarketState:
        return self.feeds.collect(symbol)

    def generate_signal(self, state: MarketState) -> Dict[str, float]:
        ensemble, scores = self.model_stack.predict(state)
        return {"ensemble": ensemble, "scores": scores, "confidence": float(abs(ensemble))}

    def execute_trade(self, state: MarketState) -> Dict:
        signal = self.generate_signal(state)
        tag = self._dna()
        trade = self.broker.execute(state, signal["ensemble"], signal["scores"], tag)
        self.reflex.record(trade)
        trade["confidence"] = signal["confidence"]
        return trade

    def ghost_trade(self, state: MarketState) -> Dict:
        return self.ghost.run(state, self._dna())

    def run_cycle(self, symbol: str) -> Dict:
        state = self.prepare_state(symbol)
        executed = self.execute_trade(state)
        ghost = self.ghost_trade(state)
        self.reflex.evaluate(executed, ghost)
        return {"executed": executed, "ghost": ghost}
