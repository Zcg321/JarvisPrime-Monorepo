from logger import log_event
import random

def vegeta_challenge():
    log_event("Vegeta Engine", "Challenger mode initiated.")
    challenge_intensity = apply_contrarian_logic()
    sharpen_entry_exit(challenge_intensity)

# Contrarian logic with intensity scaling
def apply_contrarian_logic():
    confidence_divergence = random.uniform(0.2, 1.0)  # Scale divergence: 0.2 (small), 1.0 (large)
    log_event("Vegeta Contrarian", f"Questioning council consensus. Divergence intensity: {confidence_divergence:.2f}")
    return confidence_divergence

# Entry/exit sharpening with precision score
def sharpen_entry_exit(challenge_intensity):
    precision_score = max(0.1, 1.0 - challenge_intensity * 0.5)  # Higher intensity = tighter precision
    log_event("Vegeta Sniper", f"Fine-tuning entry/exit points. Precision score: {precision_score:.2f}")

    # Override: Force council re-evaluation if challenge too high
    if challenge_intensity > 0.8:
        log_event("Vegeta Sniper", "Override triggered: Forcing council re-evaluation due to high challenge intensity.")