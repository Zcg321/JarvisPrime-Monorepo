"""Model stack for TrAId with collaborative and competitive scoring.
DNA:TRAID-MODELSTACK
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

MEMORY_FILE = Path("data/failed_trades.json")
MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
if not MEMORY_FILE.exists():
    MEMORY_FILE.write_text("{}")

SCORES_FILE = Path("data/model_scores.json")
SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
if not SCORES_FILE.exists():
    SCORES_FILE.write_text("{}")


def _load_fail_memory() -> Dict[str, int]:
    return json.loads(MEMORY_FILE.read_text())


def _load_scores() -> Dict[str, Dict[str, float]]:
    return json.loads(SCORES_FILE.read_text())


def _save_scores(data: Dict[str, Dict[str, float]]) -> None:
    SCORES_FILE.write_text(json.dumps(data, indent=2))


@dataclass
class BaseModel:
    name: str
    weight: float = 1.0
    performance: float = 1.0

    def predict(self, data: Dict) -> float:  # pragma: no cover
        raise NotImplementedError

    def adjust(self, outcome: float, confidence: float) -> None:
        self.performance = 0.95 * self.performance + 0.05 * outcome * confidence
        self.weight = max(0.1, self.performance)

    def mutate(self) -> None:  # pragma: no cover
        pass


@dataclass
class GokuModel(BaseModel):
    window: int = 14

    def predict(self, data: Dict) -> float:
        prices = np.array(data["prices"][-self.window:])
        if len(prices) < 2:
            return 0.0
        momentum = (prices[-1] - prices[0]) / (np.std(prices) + 1e-9)
        return float(np.tanh(momentum))

    def mutate(self) -> None:
        self.window = max(5, int(self.window * 1.2))


class GohanModel(BaseModel):
    """Sentiment-driven model."""

    def predict(self, data: Dict) -> float:
        return float(np.tanh(data.get("sentiment", 0.0)))


class VegetaModel(BaseModel):
    """Volatility/defense model."""

    def predict(self, data: Dict) -> float:
        prices = np.array(data["prices"])
        vol = np.std(prices) / (np.mean(prices) + 1e-9)
        return float(-np.tanh(vol))


class PiccoloModel(BaseModel):
    """Self-repair model penalizing historically failed symbols."""

    def predict(self, data: Dict) -> float:
        fails = _load_fail_memory()
        penalty = -0.05 * fails.get(data["symbol"], 0)
        return penalty


class ModelStack:
    """Ensemble of all models with competitive scoring."""

    def __init__(self) -> None:
        self.models: List[BaseModel] = [
            GokuModel("goku"),
            GohanModel("gohan"),
            VegetaModel("vegeta"),
            PiccoloModel("piccolo"),
        ]
        self._load_persisted()

    def _load_persisted(self) -> None:
        scores = _load_scores()
        for m in self.models:
            if m.name in scores:
                m.weight = scores[m.name].get("weight", m.weight)
                m.performance = scores[m.name].get("performance", m.performance)
                if isinstance(m, GokuModel):
                    m.window = scores[m.name].get("window", m.window)

    def _persist(self) -> None:
        data = {
            m.name: {
                "weight": m.weight,
                "performance": m.performance,
                **({"window": m.window} if isinstance(m, GokuModel) else {}),
            }
            for m in self.models
        }
        _save_scores(data)

    def predict(self, state) -> Tuple[float, Dict[str, float]]:
        data = state.__dict__ if hasattr(state, "__dict__") else state
        scores = {m.name: m.predict(data) for m in self.models}
        total_weight = sum(m.weight for m in self.models)
        ensemble = sum(m.weight * scores[m.name] for m in self.models) / total_weight
        return ensemble, scores

    def update(self, outcome: float, scores: Dict[str, float]) -> None:
        for m in self.models:
            conf = abs(scores[m.name])
            m.adjust(outcome, conf)
            if m.performance < 0.5:
                m.mutate()
        self._persist()

    def get_scores(self) -> Dict[str, Dict[str, float]]:
        return {
            m.name: {"weight": m.weight, "performance": m.performance}
            for m in self.models
        }

    def load_scores(self, data: Dict[str, Dict[str, float]]) -> None:
        for m in self.models:
            if m.name in data:
                m.weight = data[m.name].get("weight", m.weight)
                m.performance = data[m.name].get("performance", m.performance)
                if isinstance(m, GokuModel):
                    m.window = data[m.name].get("window", m.window)
        self._persist()
