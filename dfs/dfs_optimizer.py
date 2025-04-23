# Define DraftKings lineup slots
lineup_slots = ["PG", "SG", "SF", "PF", "C", "G", "F", "UTIL"]
salary_cap = 50000
lineup = []
current_salary = 0

# Define eligible positions for flexible slots
flex_positions = {
    "G": ["PG", "SG"],
    "F": ["SF", "PF"],
    "UTIL": ["PG", "SG", "SF", "PF", "C"]
}

# Shuffle candidates for randomness within council's risk selection
random.shuffle(candidates)

# Build lineup slot by slot
for slot in lineup_slots:
    for player in candidates:
        if player in lineup:
            continue  # Avoid duplicates

        eligible_positions = [slot] if slot in ["PG", "SG", "SF", "PF", "C"] else flex_positions[slot]

        if player["position"] in eligible_positions and (current_salary + player["salary"] <= salary_cap):
            lineup.append(player)
            current_salary += player["salary"]
            break

# Final log
log_event("DFS Optimizer", f"Final DraftKings lineup: {lineup}, Total Salary: {current_salary}")