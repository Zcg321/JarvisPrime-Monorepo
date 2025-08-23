import json
from pathlib import Path
from typing import List, Dict, Any
from prime import reflex_ancestry

BIAS_FILE = Path("logs") / "reflex_bias.json"

class Reflex:
    """Simple Reflex engine applying scoring, learning and self-checks."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        # Bias per proposal source updated via feedback
        try:
            self.source_bias = json.loads(BIAS_FILE.read_text())
        except Exception:
            self.source_bias = {}

    def score_proposal(
        self,
        weight: float,
        source_weight: float,
        affect_bias: float,
        source: str,
    ) -> float:
        return weight * source_weight * affect_bias * self.source_bias.get(source, 1.0)

    def choose_action(self, proposals: List[Dict[str, Any]], affect: str = "calm") -> Dict[str, Any]:
        """Pick the highest scoring proposal with affect bias.

        ``affect`` modifies exploration vs. exploitation:
        - ``frustrated`` slightly increases exploration (bias 1.1)
        - ``anxious`` downweights choices (bias 0.9)
        - ``confident`` boosts strong signals (bias 1.2)
        - ``calm`` leaves scores neutral.
        """

        bias = 1.0
        if affect == "frustrated":
            bias = 1.1
        elif affect == "anxious":
            bias = 0.9
        elif affect == "confident":
            bias = 1.2

        scored = []
        for p in proposals:
            risk = p.get("risk", 0)
            src = p.get("source", "")
            score = self.score_proposal(
                p.get("weight", 1.0),
                p.get("source_weight", 1.0),
                bias,
                src,
            ) / (1 + risk)
            scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[0][1] if scored else {}
        record = {"action": chosen, "scores": scored, "affect": affect}
        self.history.append(record)
        reflex_ancestry.append(record)
        return chosen

    def self_check(self, decision: Dict[str, Any]) -> Dict[str, bool]:
        """Run basic safety and resource checks before executing."""

        uses_local = decision.get("uses_local", True)
        uses_rag = decision.get("uses_rag", False)
        checklist = {
            "bankroll_ok": decision.get("bankroll", 0) >= 0,
            "tool_needed": decision.get("needs_tool", False),
            "uses_local_or_rag": uses_local or uses_rag,
            "within_risk": decision.get("risk", 0) <= decision.get("risk_limit", 1),
        }
        entry = {"self_check": checklist, "decision": decision}
        self.history.append(entry)
        reflex_ancestry.append(entry)
        return checklist

    def feedback(self, source: str, success: bool) -> float:
        """Update bias for ``source`` based on outcome.

        ``success`` increases bias; failure decreases. Bias is clipped to
        ``[0.5, 2.0]``. Returns the new bias for convenience.
        """

        bias = self.source_bias.get(source, 1.0)
        bias *= 1.05 if success else 0.95
        bias = min(2.0, max(0.5, bias))
        self.source_bias[source] = bias
        self.history.append({"feedback": {"source": source, "success": success, "bias": bias}})
        self._save_biases()
        return bias

    def _save_biases(self) -> None:
        """Persist bias state so learning survives restarts."""
        try:
            BIAS_FILE.parent.mkdir(parents=True, exist_ok=True)
            BIAS_FILE.write_text(json.dumps(self.source_bias))
        except Exception:
            pass
