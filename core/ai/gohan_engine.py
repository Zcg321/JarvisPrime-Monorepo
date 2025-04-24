from logger import log_event
import random

# Gohan Support Engine
def gohan_support(aggression_level=1.0):
    log_event("Gohan Engine", f"Support mode engaged. Aggression level: {aggression_level}")
    run_divergence_paths()
    apply_risk_buffer(aggression_level)

# Divergence logic
def run_divergence_paths():
    divergence_intensity = random.uniform(0.5, 1.5)
    scenario = random.choice(["bullish divergence", "bearish trap", "sideways compression"])
    log_event("Gohan Divergence", f"Exploring alternate scenario forks. Intensity: {divergence_intensity:.2f}, Scenario: {scenario}")
    # Future: Add this to Tool-Builder AI memory module

# Risk buffer logic
def apply_risk_buffer(aggression_level):
    buffer_strength = max(0.1, 1.0 - aggression_level * 0.2)
    log_event("Gohan Risk", f"Applying protective buffers. Strength: {buffer_strength:.2f}")

    # Protective override trigger
    if buffer_strength > 0.8:
        log_event("Gohan Risk", "Override triggered: Aggressive signals dampened.")