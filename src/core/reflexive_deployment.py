from core.logger import log_event
from core.surgecell_handler import allocate_power
import random

# Logic variant registry
logic_registry = {
    "dfs": [],
    "traid": [],
    "swarm": []
}

# Register logic variant
def register_logic(module, logic_name, performance_metrics):
    if module not in logic_registry:
        logic_registry[module] = []  # Initialize an empty list if module does not exist

    logic_registry[module].append({
        "name": logic_name,
        "metrics": performance_metrics
    })

    log_event("Reflexive Deployment", f"Registered {logic_name} for {module} with metrics {performance_metrics}")

# Evaluate and weight logic variants
def evaluate_logic(module):
    log_event("Reflexive Deployment", f"Evaluating logic for {module}...")
    
    allocate_power("reflexive_deployment")  # SurgeCell boost (power allocation)
    
    variants = logic_registry.get(module, [])
    if not variants:
        log_event("Reflexive Deployment", "No logic variants registered.")
        return None

    totals = {key: sum(v["metrics"].get(key, 0) for v in variants) for key in 
              ["profitability", "consistency", "edge_discovery", "deployment_win_rate"]}

    for variant in variants:
        profit_weight = variant["metrics"].get("profitability", 0) / totals["profitability"] if totals["profitability"] else 0
        consistency_weight = variant["metrics"].get("consistency", 0) / totals["consistency"] if totals["consistency"] else 0
        edge_weight = variant["metrics"].get("edge_discovery", 0) / totals["edge_discovery"] if totals["edge_discovery"] else 0
        win_rate_weight = variant["metrics"].get("deployment_win_rate", 0) / totals["deployment_win_rate"] if totals["deployment_win_rate"] else 0

        variant["weight"] = (
            0.4 * profit_weight +
            0.3 * consistency_weight +
            0.2 * edge_weight +
            0.1 * win_rate_weight
        )

        log_event("Reflexive Deployment", f"{variant['name']} weighted at {variant['weight']:.2f}")

    weights = [v["weight"] for v in variants]
    if max(weights) - min(weights) < 0.05:  # Convergence threshold
        log_event("Reflexive Deployment", "Override loop triggered: Weight convergence detected. Re-sampling required.")

    return variants
