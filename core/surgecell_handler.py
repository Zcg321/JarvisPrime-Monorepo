from reflex_chain_handler import trigger_reflex_chain

def allocate_power(target_module, priority_level="normal"):
    print(f"[SurgeCell] Allocating power to {target_module} at {priority_level} priority.")
    # Reflex chain triggers when priority is high
    if priority_level == "high":
        trigger_reflex_chain(source="SurgeCell", targets=[target_module])