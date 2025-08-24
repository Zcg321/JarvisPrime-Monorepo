"""Persistence utilities for TrAId state.
DNA:TRAID-SAVEPOINT
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from .model_stack import ModelStack
from .reflex import ReflexEngine
from .broker import SimBroker

STATE_FILE = Path("savepoint.json")


def save_state(model_stack: ModelStack, reflex: ReflexEngine, broker: SimBroker, path: Path = STATE_FILE) -> None:
    state = {
        "model_scores": model_stack.get_scores(),
        "fail_memory": reflex.fail_memory,
        "trades": broker.trades,
        "regret": reflex.regret,
    }
    path.write_text(json.dumps(state, indent=2))


def load_state(model_stack: ModelStack, reflex: ReflexEngine, broker: SimBroker, path: Path = STATE_FILE) -> None:
    if not path.exists():
        return
    data: Dict = json.loads(path.read_text())
    model_stack.load_scores(data.get("model_scores", {}))
    reflex.fail_memory = data.get("fail_memory", {})
    broker.trades = data.get("trades", [])
    reflex.regret = data.get("regret", {})
