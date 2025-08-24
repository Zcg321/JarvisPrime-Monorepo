import json
from pathlib import Path
from typing import List, Dict, Any

import yaml
from prime import reflex_ancestry
from src.savepoint.logger import savepoint_log
from src.serve import alerts, logging as slog
from . import ledger

BIAS_FILE = Path("logs") / "reflex_bias.json"
POLICY_FILE = Path("configs/bankroll.yaml")
RISK_FILE = Path("configs/risk.yaml")

try:
    POLICY = yaml.safe_load(POLICY_FILE.read_text())
except Exception:
    POLICY = {}
try:
    RISK = yaml.safe_load(RISK_FILE.read_text())
except Exception:
    RISK = {}

class Reflex:
    """Simple Reflex engine applying scoring, learning and self-checks."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        # Bias per proposal source updated via feedback
        try:
            self.source_bias = json.loads(BIAS_FILE.read_text())
        except Exception:
            self.source_bias = {}
        self.policy = POLICY

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

    def self_check(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Run basic safety and resource checks before executing."""

        uses_local = decision.get("uses_local", True)
        uses_rag = decision.get("uses_rag", False)
        bankroll = float(decision.get("bankroll", 0))
        wager = float(decision.get("wager", 0))
        pnl = ledger.day_pnl()
        decision["day_win"] = max(pnl, 0.0)
        decision["day_loss"] = max(-pnl, 0.0)
        checklist = {
            "bankroll_ok": bankroll - wager >= 0,
            "safety_ok": not decision.get("danger", False),
            "tool_needed": decision.get("needs_tool", False),
            "uses_local_or_rag": uses_local or uses_rag,
            "within_risk": decision.get("risk", 0) <= decision.get("risk_limit", 1),
        }

        blocked = False
        reason = ""
        policy = self.policy
        if policy:
            allow = set(policy.get("allow_when_affect", []))
            affect = decision.get("affect")
            if allow and affect not in allow:
                blocked = True
                reason = "affect"
            elif wager > bankroll * float(policy.get("unit_fraction", 1.0)):
                blocked = True
                reason = "unit"
            elif decision["day_loss"] > bankroll * float(policy.get("stop_loss_daily", 1.0)):
                blocked = True
                reason = "stop_loss"
            elif decision["day_win"] > bankroll * float(policy.get("stop_win_lock", 1.0)):
                blocked = True
                reason = "stop_win"
        if not blocked and decision.get("risk_stats") and RISK:
            stats = decision["risk_stats"]
            if stats.get("drawdown_p95", 0) > float(RISK.get("max_drawdown_p95", 1.0)):
                blocked = True
                reason = "risk_drawdown"
            elif stats.get("variance", 0) > float(RISK.get("max_variance", float("inf"))):
                blocked = True
                reason = "risk_variance"
            elif stats.get("ev", 0) < float(RISK.get("require_ev_ge", -float("inf"))):
                blocked = True
                reason = "risk_ev"
        checklist["policy_ok"] = not blocked
        if blocked:
            checklist["blocked"] = True
            checklist["reason"] = reason
            savepoint_log("risk_gate_block", {"reason": reason})
            alerts.log_event("risk_gate_block", reason)
            slog.alert("risk gate block", component="reflex", reason=reason)
        else:
            checklist["blocked"] = False
            if wager:
                ledger.record(wager, decision.get("outcome"))

        entry = {"self_check": checklist, "decision": decision}
        self.history.append(entry)
        reflex_ancestry.append(entry)
        try:
            savepoint_log("reflex_self_check", entry, decision.get("affect"), decision.get("bankroll"))
        except Exception:
            pass
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
