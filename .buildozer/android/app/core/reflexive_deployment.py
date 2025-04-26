from logger import log_event
from surgecell_monitor import request_power_boost
import random

# Logic variant registry
logic_registry = {
    "dfs": [],
    "traid": [],
    "swarm": []
}

# Register logic variant
def register_logic(module, logic_name, performance_metrics):
    logic_registry[module].append({
        "name": logic_name,
        "metrics": performance_metrics
    })
    log_event("Reflexive Deployment", f"Registered {logic_name} for {module} with metrics {performance_metrics}")

# Evaluate and weight logic variants
def evaluate_logic(module):
    log_event("Reflexive Deployment", f"Evaluating logic for {module}...")
    request_power_boost("reflexive_deployment")  # SurgeCell boost
    variants = logic_registry[module]
    if not variants:
        log_event("Reflexive Deployment", "No logic variants registered.")
        return None

    # Totals with ripple filtering
    totals = {key: sum(v["metrics"][key] for v in variants) for key in ["profitability", "consistency", "edge_discovery", "deployment_win_rate"]}
    
    for variant in variants:
        profit_weight = variant["metrics"]["profitability"] / totals["profitability"] if totals["profitability"] else 0
        consistency_weight = variant["metrics"]["consistency"] / totals["consistency"] if totals["consistency"] else 0
        edge_weight = variant["metrics"]["edge_discovery"] / totals["edge_discovery"] if totals["edge_discovery"] else 0
        win_rate_weight = variant["metrics"]["deployment_win_rate"] / totals["deployment_win_rate"] if totals["deployment_win_rate"] else 0

        # Composite weighting: sharpened with win rate and divergence factors
        variant["weight"] = (
            0.4 * profit_weight +
            0.3 * consistency_weight +
            0.2 * edge_weight +
            0.1 * win_rate_weight
        )

        log_event("Reflexive Deployment", f"{variant['name']} weighted at {variant['weight']:.2f}")

    # Override loop: check for too-close convergence
    weights = [v["weight"] for v in variants]
    if max(weights) - min(weights) < 0.05:  # Ripple filter
        log_event("Reflexive Deployment", "Override loop triggered: Weight convergence detected. Re-sampling required.")

    return variants

# Mock logic registration for DFS
register_logic("dfs", "standard_logic", {
    "profitability": random.uniform(1.0, 2.0),
    "consistency": random.uniform(0.7, 1.0),
    "edge_discovery": random.uniform(0.1, 0.5),
    "deployment_win_rate": random.uniform(0.6, 0.9)
})

register_logic("dfs", "contrarian_logic", {
    "profitability": random.uniform(0.8, 1.8),
    "consistency": random.uniform(0.5, 0.9),
    "edge_discovery": random.uniform(0.3, 0.7),
    "deployment_win_rate": random.uniform(0.5, 0.85)
})

evaluate_logic("dfs")
