from ai.goku_engine import goku_boost
from ai.gohan_engine import gohan_support
from ai.vegeta_engine import vegeta_challenge
from ai.piccolo_engine import piccolo_harmonize

def trigger_reflex_chain(source, targets):
    print(f"[Reflex Chain] Triggered by {source}. Target modules: {targets}")
    for target in targets:
        print(f"  - Engaging {target} with adaptive power routing...")
        if target.lower() == "goku":
            goku_boost()
        elif target.lower() == "gohan":
            gohan_support()
        elif target.lower() == "vegeta":
            vegeta_challenge()
        elif target.lower() == "piccolo":
            piccolo_harmonize()