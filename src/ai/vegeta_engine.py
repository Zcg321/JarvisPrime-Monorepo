from core.logger import log_event
import random

def vegeta_challenge(sentiment_divergence=0.0):
    log_event("Vegeta Engine", "Challenger mode initiated.")
    challenge_intensity = apply_contrarian_logic()
    sharpen_entry_exit(challenge_intensity, sentiment_divergence)
    compress_feedback(challenge_intensity)

# Contrarian logic with ripple/noise filtering
def apply_contrarian_logic():
    base_divergence = random.uniform(0.2, 1.0)
    divergence_intensity = apply_noise_filters(base_divergence)
    log_event("Vegeta Contrarian", f"Questioning council consensus. Divergence intensity: {divergence_intensity:.2f}")
    record_tool_builder("ConfidenceDivergence", {"intensity": divergence_intensity})
    return divergence_intensity

# Entry/exit sharpening with sentiment divergence adjustment
def sharpen_entry_exit(challenge_intensity, sentiment_divergence):
    precision_score = max(0.1, 1.0 - (challenge_intensity * 0.5 + sentiment_divergence * 0.1))
    log_event("Vegeta Sniper", f"Fine-tuning entry/exit points. Precision score: {precision_score:.2f}")

    # Override: Force council re-evaluation if challenge too high
    if challenge_intensity > 0.8:
        log_event("Vegeta Sniper", "Override triggered: Forcing council re-evaluation due to high challenge intensity.")

# Goku/Gohan feedback compression layer
def compress_feedback(challenge_intensity):
    compression_factor = 1.0 / (1.0 + challenge_intensity)
    log_event("Vegeta Compression", f"Applying feedback compression. Factor: {compression_factor:.2f}")

# Ripple/Noise filter logic
def apply_noise_filters(value):
    if random.random() < 0.3:
        noise_adjustment = random.uniform(-0.05, 0.05)
        value += noise_adjustment
    return max(0.0, min(1.0, value))

# Tool-Builder AI Memory Hook
def record_tool_builder(tag, data):
    log_event("Tool-Builder", f"Recorded {tag}: {data}")
