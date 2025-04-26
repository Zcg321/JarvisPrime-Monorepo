from ai.goku_engine import goku_boost
from ai.gohan_engine import gohan_support
from ai.vegeta_engine import vegeta_challenge
from ai.piccolo_engine import piccolo_harmonize
from surgecell_monitor import request_power_boost
from logger import log_event

def trigger_reflex_chain(source, targets):
    """
    Triggers the reflex chain by engaging specific target modules based on their names.
    This boosts the power and adapts the response based on the target.
    """
    log_event("Reflex Chain", f"Triggered by {source}. Target modules: {targets}")

    # SurgeCell boost
    request_power_boost("reflex_chain")

    # Trigger the appropriate response for each target
    for target in targets:
        target_lower = target.lower()
        log_event("Reflex Chain", f"Engaging {target_lower} with adaptive power routing...")

        # Adaptive behavior based on the target
        if target_lower == "goku":
            goku_boost()
        elif target_lower == "gohan":
            gohan_support()
        elif target_lower == "vegeta":
            vegeta_challenge()
        elif target_lower == "piccolo":
            piccolo_harmonize()
        else:
            log_event("Reflex Chain", f"Unknown target module: {target}")
