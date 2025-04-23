from ai.goku_engine import goku_boost from ai.gohan_engine import gohan_support from ai.vegeta_engine import vegeta_challenge from ai.piccolo_engine import piccolo_harmonize from logger import log_event import random

Shared bankroll state

bankroll_state = {"total_bankroll": 1000, "aggression_level": 1.0}

def allocate_stake(base_percent=5): bankroll = bankroll_state["total_bankroll"] aggression = bankroll_state["aggression_level"]

# Base stake sizing
stake = bankroll * (base_percent / 100)

# Council-driven adjustments
goku_boost(); stake *= 1.5
gohan_support(); stake *= 0.8
vegeta_challenge()
if random.random() < 0.3: stake *= 1.2
piccolo_harmonize(); stake = min(stake, bankroll * 0.1)

# Apply aggression level
stake *= aggression
stake = max(1, round(stake))

log_event("Bankroll AI", f"Allocated Stake: ${stake}")
return stake

def adjust_aggression(profit): # Adjust aggression based on profit outcomes if profit > 0: bankroll_state["aggression_level"] += 0.1 log_event("Bankroll AI", "Increasing aggression.") else: bankroll_state["aggression_level"] = max(0.8, bankroll_state["aggression_level"] - 0.1) log_event("Bankroll AI", "Reducing aggression.")
