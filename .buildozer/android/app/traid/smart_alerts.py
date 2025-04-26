from trade_scoring_engine import score_trade
from logger import log_event

def trigger_alert(trade_data):
    log_event("Smart Alerts", "Processing trade signal...")

    score = score_trade(trade_data)

    # Dynamic adjustments for alert thresholds based on council logic
    # Goku boosts aggressive alerts, Gohan adds risk buffers, Vegeta challenges overly confident signals, Piccolo harmonizes
    if score >= 70:
        log_event("Smart Alerts", f"ALERT: High-confidence trade signal! Score: {score}")
    elif score >= 50:
        log_event("Smart Alerts", f"NOTICE: Moderate-confidence trade signal. Score: {score}")
    else:
        log_event("Smart Alerts", f"PASS: Low-confidence trade signal. Score: {score}")

    # Goku and Vegeta's influence for boost and contrarian logic
    # Goku influence (aggressive)
    if score >= 70:
        log_event("Smart Alerts", "Goku influence: Boosting alert confidence due to aggressive market signals.")
    
    # Gohan influence (risk buffer)
    if score < 50:
        log_event("Smart Alerts", "Gohan influence: Adding risk buffer to the low-confidence signal.")

    # Vegeta influence (contrarian challenge)
    if score >= 80:
        log_event("Smart Alerts", "Vegeta influence: Challenging high-confidence signal due to market conditions.")

    # Piccolo harmonizing influence
    if score > 90:
        log_event("Smart Alerts", "Piccolo influence: Harmonizing alert thresholds to prevent overreaction.")
