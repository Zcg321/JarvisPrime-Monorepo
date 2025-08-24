# reflex_chain.py

# Initial Council weights
council_weights = {
    'goku': 1.05,
    'gohan': 1.10,
    'vegeta': 1.15,
    'piccolo': 0.90
}

# Previous score tracker
previous_score = None

def goku_boost(metrics, weight):
    metrics['profitability'] *= weight
    return metrics

def gohan_support(metrics, weight):
    metrics['consistency'] *= weight
    return metrics

def vegeta_challenge(metrics, weight):
    metrics['edge_discovery'] *= weight
    return metrics

def piccolo_harmonize(metrics, weight):
    if 'variance' in metrics:
        metrics['variance'] *= weight
    return metrics

def auto_tune_council(current_score):
    global previous_score
    if previous_score is not None:
        if current_score < previous_score:
            council_weights['goku'] += 0.01
            council_weights['gohan'] += 0.01
            council_weights['vegeta'] += 0.01
            council_weights['piccolo'] -= 0.01
        else:
            council_weights['goku'] -= 0.005
            council_weights['gohan'] -= 0.005
            council_weights['vegeta'] -= 0.005
            council_weights['piccolo'] += 0.005
    previous_score = current_score  # Always update after comparison

def run_council(metrics, current_score):
    auto_tune_council(current_score)
    print(f"[Council Reflex] Weights after tuning: {council_weights}")  # Print after tuning
    metrics = goku_boost(metrics, council_weights['goku'])
    metrics = gohan_support(metrics, council_weights['gohan'])
    metrics = vegeta_challenge(metrics, council_weights['vegeta'])
    metrics = piccolo_harmonize(metrics, council_weights['piccolo'])
    return metrics
