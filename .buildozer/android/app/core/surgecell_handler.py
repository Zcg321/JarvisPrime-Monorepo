from reflex_chain_handler_final import trigger_reflex_chain
from logger import log_event
import random

def allocate_power(target_module, priority_level="normal"):
    load_factor = random.uniform(0.5, 1.5)  # Simulate system load variability
    log_event("SurgeCell", f"Allocating power to {target_module} at {priority_level} priority. Load factor: {load_factor:.2f}")

    if priority_level == "high":
        # Trigger Goku/Gohan compression reflex chains for added boost
        trigger_reflex_chain(source="SurgeCell", targets=[target_module, "goku", "gohan"])

    # Override dampening logic
    if load_factor > 1.3:
        log_event("SurgeCell", "Override triggered: Power demand spike detected. Applying dampening to stabilize flow.")
