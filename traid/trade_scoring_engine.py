from ai.goku_engine import goku_boost
from ai.gohan_engine import gohan_support
from ai.vegeta_engine import vegeta_challenge
from ai.piccolo_engine import piccolo_harmonize
from logger import log_event
import random

def score_trade(trade_data):
    log_event("Trade Scoring Engine", "Scoring trade with AI council...")

    # Initial trade score baseline (1-100 scale)
    base_score = random.randint(40, 60)

    # Council adjusts the trade score
    goku_boost()
    base_score += 10  # Goku boosts confidence

    gohan_support()
    base_score -= 5  # Gohan adds cautious adjustment

    vegeta_challenge()
    base_score -= random.randint(0, 10)  # Vegeta questions the score

    piccolo_harmonize()
    base_score = max(min(base_score, 100), 0)  # Piccolo balances to valid range

    log_event("Trade Scoring Engine", f"Final trade score: {base_score}")
    return base_score