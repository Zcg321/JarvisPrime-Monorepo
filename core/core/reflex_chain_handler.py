import random
from logger import log_event

def trigger_reflex_chain(source, targets):
    log_event("Reflex Chain", f"Triggered by {source}. Target modules: {targets}")
    for target in targets:
        stress_level = simulate_stress(target)
        power_allocation = adaptive_power_routing(stress_level)
        log_event("Reflex Chain", f"Engaging {target} | Stress Level: {stress_level:.2f}, Power Allocated: {power_allocation:.2f}")

        # Override trigger if stress too high
        if stress_level > 0.8:
            log_event("Reflex Chain", f"Override: {target} load too high. Rerouting power or delaying activation.")

# Simulate stress level (stub for future load detection)
def simulate_stress(module):
    return random.uniform(0.2, 1.0)  # Stress level: 0.2 (low) to 1.0 (high)

# Adaptive power routing logic
def adaptive_power_routing(stress_level):
    return max(0.1, 1.0 - stress_level)  # Higher stress = less power routed