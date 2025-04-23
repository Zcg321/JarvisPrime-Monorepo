from trade_scoring_engine import score_trade
from logger import log_event

def trigger_alert(trade_data):
    log_event("Smart Alerts", "Processing trade signal...")

    score = score_trade(trade_data)

    # Alert threshold logic
    if score >= 70:
        log_event("Smart Alerts", f"ALERT: High-confidence trade signal! Score: {score}")
    elif score >= 50:
        log_event("Smart Alerts", f"NOTICE: Moderate-confidence trade signal. Score: {score}")
    else:
        log_event("Smart Alerts", f"PASS: Low-confidence trade signal. Score: {score}")