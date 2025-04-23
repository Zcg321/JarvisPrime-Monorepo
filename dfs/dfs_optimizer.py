from ai.goku_engine import goku_boost from ai.gohan_engine import gohan_support from ai.vegeta_engine import vegeta_challenge from ai.piccolo_engine import piccolo_harmonize from logger import log_event from bankroll_ai import allocate_stake, adjust_aggression import random import requests import csv from dff_scraper import scrape_dff_csv

Fetch player data from DFF CSV

def fetch_csv_player_data(filepath): log_event("DFS Optimizer", "Loading player data from CSV...") player_data = [] try: with open(filepath, mode='r') as file: reader = csv.DictReader(file) for row in reader: player_data.append({ "name": row["Player"], "position": row["POS"], "salary": int(row["SALARY"]), "projection": float(row["FPTS"]), "ownership": random.uniform(5, 30)  # Placeholder for ownership (replace with scraped) }) except Exception as e: log_event("DFS Optimizer", f"CSV load failed: {e}") return player_data

Weighted logic mesh for lineup optimizers

def standard_lineup_logic(player_pool): # Standard logic (current) lineup_slots = ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"] salary_cap = 50000 lineup, current_salary = [], 0 flex_positions = {"G": ["PG", "SG"], "F": ["SF", "PF"], "UTIL": ["PG", "SG", "SF", "PF", "C"]}

candidates = player_pool.copy()
random.shuffle(candidates)

for slot in lineup_slots:
    for player in candidates:
        if player in lineup:
            continue
        eligible_positions = [slot] if slot in ["PG", "SG", "SF", "PF", "C"] else flex_positions[slot]
        if player["position"] in eligible_positions and (current_salary + player["salary"] <= salary_cap):
            lineup.append(player)
            current_salary += player["salary"]
            break

return lineup, current_salary

def contrarian_lineup_logic(player_pool): # Contrarian variation (alternative logic) lineup, current_salary = standard_lineup_logic(player_pool) # Force one low-owned player if not any(p["ownership"] < 10 for p in lineup): low_owned = [p for p in player_pool if p["ownership"] < 10 and p not in lineup] if low_owned: highest_owned = max(lineup, key=lambda x: x["ownership"]) contrarian_player = random.choice(low_owned) current_salary -= highest_owned["salary"] current_salary += contrarian_player["salary"] lineup.remove(highest_owned) lineup.append(contrarian_player) return lineup, current_salary

def optimize_lineup(): log_event("DFS Optimizer", "Starting lineup optimization with weighted logic mesh...")

# Scrape and load CSV player data
scrape_dff_csv()
player_pool = fetch_csv_player_data("projections.csv")

# Council adjusts strategy
goku_boost()
gohan_support()
vegeta_challenge()
piccolo_harmonize()

num_lineups = 5
all_lineups = []

for i in range(num_lineups):
    stake = allocate_stake()
    contest_types = ["GPP", "Single-Entry", "3-Max", "Cash", "Satellite"]
    contest_type = random.choice(contest_types)
    log_event("DFS Optimizer", f"Lineup {i+1} - Stake: ${stake}, Contest: {contest_type}")

    # Apply weighted mesh logic
    if contest_type == "GPP":
        lineup, current_salary = contrarian_lineup_logic(player_pool)
        logic_weight = "Contrarian Logic (70%)"
    else:
        lineup, current_salary = standard_lineup_logic(player_pool)
        logic_weight = "Standard Logic (90%)"

    avg_ownership = sum(p["ownership"] for p in lineup) / len(lineup)

    # ROI simulation
    roi_lookup = {"GPP": {"aggressive": 2.5, "balanced": 1.5, "conservative": 0.5, "contrarian": 3.0}}
    risk_profile = "balanced"
    goku_boost(); risk_profile = "aggressive"
    gohan_support(); risk_profile = "conservative" if risk_profile == "aggressive" else risk_profile
    roi = roi_lookup.get(contest_type, {}).get(risk_profile, 1.0)
    variance = random.uniform(0.8, 1.2)
    adjusted_roi = roi * variance
    profit = stake * adjusted_roi - stake

    adjust_aggression(profit)

    all_lineups.append({"lineup": lineup, "salary": current_salary, "ownership": avg_ownership, "profit": profit, "logic_weight": logic_weight})

# Post-contest review
total_profit = sum(l["profit"] for l in all_lineups)
avg_ownership = sum(l["ownership"] for l in all_lineups) / len(all_lineups)
avg_projection = sum(sum(p["projection"] for p in l["lineup"]) / len(l["lineup"]) for l in all_lineups) / len(all_lineups)
log_event("DFS Review", f"Total Profit: ${total_profit:.2f}, Avg Ownership: {avg_ownership:.2f}%, Avg Projection: {avg_projection:.2f}")

