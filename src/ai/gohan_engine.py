from core.logger import log_event
import random

# Gohan Support Engine
def gohan_support(aggression_level=1.0, sentiment_divergence=0.0):
    log_event("Gohan Engine", f"Support mode engaged. Aggression level: {aggression_level}")
    run_divergence_paths(sentiment_divergence)
    apply_risk_buffer(aggression_level)

# Divergence logic with Sentiment + Ripple/Noise filters
def run_divergence_paths(sentiment_divergence):
    divergence_intensity = random.uniform(0.5, 1.5) + sentiment_divergence
    scenario = apply_noise_filters(random.choice(["bullish divergence", "bearish trap", "sideways compression"]))
    log_event("Gohan Divergence", f"Exploring alternate scenario forks. Intensity: {divergence_intensity:.2f}, Scenario: {scenario}")
    # Tool-Builder AI learns from divergence
    record_tool_builder("DivergencePath", {"intensity": divergence_intensity, "scenario": scenario})

# Ripple/Noise filter logic
def apply_noise_filters(scenario):
    # Inject ripple/noise distortion
    if random.random() < 0.2:
        scenario += " [noise-adjusted]"
    return scenario

# Risk buffer logic with Goku feedback compression
def apply_risk_buffer(aggression_level):
    compression = goku_feedback_compression()
    buffer_strength = max(0.1, (1.0 - aggression_level * 0.2) * compression)
    log_event("Gohan Risk", f"Applying protective buffers. Strength: {buffer_strength:.2f}")

    # Protective override trigger
    if buffer_strength > 0.8:
        log_event("Gohan Risk", "Override triggered: Aggressive signals dampened.")

# Goku Feedback Compression Layer
def goku_feedback_compression():
    return random.uniform(0.85, 1.15)

# Tool-Builder AI Memory Hook
def record_tool_builder(tag, data):
    log_event("Tool-Builder", f"Recorded {tag}: {data}")
