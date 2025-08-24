# surgecell_monitor.py

from core.logger import log_event
import random

# Function to simulate and allocate power to target modules based on priority
def allocate_power(target_module, priority_level="normal"):
    """
    Simulates power allocation based on priority level.
    Higher priority triggers Goku/Gohan compression reflex chains for an added boost.
    If the system load is too high, dampening logic is applied.
    """
    load_factor = random.uniform(0.5, 1.5)  # Simulate system load variability
    log_event("SurgeCell", f"Allocating power to {target_module} at {priority_level} priority. Load factor: {load_factor:.2f}")

    # Apply dampening if system load factor exceeds threshold
    if load_factor > 1.3:
        log_event("SurgeCell", "Override triggered: Power demand spike detected. Applying dampening to stabilize flow.")
        # Optionally, you can add logic here to actually dampen the power allocation
        # For example, applying a load balance algorithm to reduce power to non-critical modules.

# Example of logging power allocation events
def log_power_allocation(target_module, priority_level="normal"):
    print(f"[SurgeCell Monitor] Allocating power to {target_module} at {priority_level} priority.")
