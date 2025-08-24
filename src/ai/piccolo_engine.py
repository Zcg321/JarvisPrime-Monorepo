from core.logger import log_event
import random

def piccolo_harmonize(sentiment_divergence=0.0):
    log_event("Piccolo Engine", "Harmonization sequence active.")
    conflict_level = resolve_conflicts()
    balance_council_outputs(conflict_level, sentiment_divergence)

# Conflict resolution with ripple/noise filtering
def resolve_conflicts():
    base_conflict = random.uniform(0.1, 1.0)
    conflict_severity = apply_noise_filters(base_conflict)
    conflict_scenario = random.choice(["minor divergence", "strategy standoff", "full council split"])
    log_event("Piccolo Resolve", f"Conflict detected: {conflict_scenario}, Severity: {conflict_severity:.2f}")
    record_tool_builder("ConflictSeverity", {"severity": conflict_severity, "scenario": conflict_scenario})
    return conflict_severity

# Council output balancing with sentiment divergence
def balance_council_outputs(conflict_severity, sentiment_divergence):
    harmony_index = max(0, 1.0 - (conflict_severity + sentiment_divergence * 0.1))
    log_event("Piccolo Balance", f"Council harmony index: {harmony_index:.2f}")

    # Override: Dampen outputs if harmony too low
    if harmony_index < 0.3:
        log_event("Piccolo Balance", "Override triggered: Damping extreme council outputs for stability.")

# Ripple/Noise filter logic
def apply_noise_filters(value):
    if random.random() < 0.25:
        noise_adjustment = random.uniform(-0.05, 0.05)
        value += noise_adjustment
    return max(0.0, min(1.0, value))  # Keep severity within bounds

# Tool-Builder AI Memory Hook
def record_tool_builder(tag, data):
    log_event("Tool-Builder", f"Recorded {tag}: {data}")
