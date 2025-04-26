from ai.goku_engine import goku_boost
from ai.gohan_engine import gohan_support
from ai.vegeta_engine import vegeta_challenge
from ai.piccolo_engine import piccolo_harmonize
from logger import log_event
import random

# Shared bankroll state
bankroll_state = {"total_bankroll": 1000, "aggression_level": 1.0}

# Allocate stake with council adjustments
def allocate_stake(base_percent=5):
    bankroll = bankroll_state["total_bankroll"]
    aggression = bankroll_state["aggression_level"]

    # Base stake sizing
    stake = bankroll * (base_percent / 100)

    # Council-driven adjustments
    goku_boost(aggression)
    stake *= 1.5  # Goku boosts stake

    gohan_support(aggression)
    stake *= 0.8  # Gohan buffers risk

    vegeta_challenge()
    if random.random() < 0.3:
        stake *= 1.2  # Vegeta adds contrarian edge

    piccolo_harmonize()
    stake = min(stake, bankroll * 0.1)  # Piccolo caps max stake for harmony

    # Apply aggression level
    stake *= aggression
    stake = max(1, round(stake))

    log_event("Bankroll AI", f"Allocated Stake: ${stake}")
    return stake

# Adjust aggression based on profit outcomes
def adjust_aggression(profit):
    if profit > 0:
        bankroll_state["aggression_level"] += 0.1
        log_event("Bankroll AI", "Increasing aggression.")
    else:
        bankroll_state["aggression_level"] = max(0.8, bankroll_state["aggression_level"] - 0.1)
        log_event("Bankroll AI", "Reducing aggression.")

# Log aggression state
log_event("Bankroll AI", f"Current Aggression Level: {bankroll_state['aggression_level']:.2f}")

# Reflexive bankroll adjustment (future-ready for Tool-Builder AI)
def reflexive_bankroll_adjustment():
    # Placeholder: Dynamically adjust bankroll based on past performance
    performance_factor = random.uniform(0.95, 1.05)
    bankroll_state["total_bankroll"] *= performance_factor
    log_event("Bankroll AI", f"Reflexive bankroll adjustment applied. New total bankroll: ${bankroll_state['total_bankroll']:.2f}")
