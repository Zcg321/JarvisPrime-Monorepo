from logger import log_event
import random

class ReflexCascadeEngine:
    def __init__(self, arena):
        self.arena = arena  # Arena contains logic modules

    def execute_reflex_sequence(self, conflict_result):
        # Determine weight deltas based on arena scoring
        diff = abs(conflict_result['scores'][0] - conflict_result['scores'][1])
        intensity = min(max(diff / 10.0, 0.01), 0.15)  # Ensure intensity is within a reasonable range

        # Cascade response triggers across modules
        for module in self.arena.logic_modules:
            if module.name == conflict_result['winner']:
                module.adjust_weight(intensity)  # Winner gets a boost
            elif module.name == conflict_result['loser']:
                module.adjust_weight(-intensity)  # Loser gets penalized
            else:
                ripple = random.uniform(-0.01, 0.01)  # Ripple effects for other modules
                module.adjust_weight(ripple)

        # Log the cascade event
        log_event("ReflexCascade", f"Cascade triggered with intensity {intensity:.3f}. Adjustments applied across modules.")

    def trigger_on_cycle_completion(self, results):
        # Run cascade for each result in the cycle
        for result in results:
            self.execute_reflex_sequence(result)

        log_event("ReflexCascade", "All cascades executed following arena cycle.")
