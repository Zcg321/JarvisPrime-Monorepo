from goku_engine import goku_boost

def trigger_reflex_chain(source, targets):
    print(f"[Reflex Chain] Triggered by {source}. Target modules: {targets}")
    for target in targets:
        print(f"  - Engaging {target} with adaptive power routing...")
        if target.lower() == "goku":
            goku_boost()