from ai.goku_engine import goku_boost
from ai.gohan_engine import gohan_support
from ai.vegeta_engine import vegeta_challenge
from ai.piccolo_engine import piccolo_harmonize
from core.surgecell_monitor import request_power_boost
from core.logger import log_event

def trigger_reflex_chain(source, targets):
    log_event("Reflex Chain", f"Triggered by {source}. Target modules: {targets}")
    request_power_boost("reflex_chain")  # SurgeCell boost

    for target in targets:
        target_lower = target.lower()
        log_event("Reflex Chain", f"Engaging {target_lower} with adaptive power routing...")
        
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
