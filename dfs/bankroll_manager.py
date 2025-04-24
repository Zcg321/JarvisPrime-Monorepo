from logger import log_event

def manage_bankroll(current_balance, risk_level="medium", contest_type="GPP"):
    log_event("Bankroll Manager", f"Managing bankroll. Balance: ${current_balance}, Risk: {risk_level}, Contest: {contest_type}")

    # Risk profile scaling
    risk_multipliers = {"conservative": 0.03, "medium": 0.05, "aggressive": 0.1}
    base_percent = risk_multipliers.get(risk_level, 0.05)

    # Contest tier adjustment
    contest_adjustment = {"Cash": 0.8, "GPP": 1.2, "3-Max": 1.0, "Satellite": 1.1}
    contest_factor = contest_adjustment.get(contest_type, 1.0)

    # Calculate stake
    raw_stake = current_balance * base_percent * contest_factor

    # Apply stake cap and floor
    stake = min(max(raw_stake, current_balance * 0.01), current_balance * 0.15)

    log_event("Bankroll Manager", f"Calculated stake: ${stake:.2f}")

    # Future: Memory hook for Tool-Builder AI

    return stake

# Example usage:
# manage_bankroll(1000, risk_level=\"aggressive\", contest_type=\"Cash\")