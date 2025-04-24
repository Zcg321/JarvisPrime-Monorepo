# Conflict Arena (Adaptive Survival Simulator) - Upgraded Version
from logger import log_event
import random

class ConflictArena:
    def __init__(self, ai_council, logic_modules, hyperbolic_chamber):
        self.ai_council = ai_council  # [Goku, Gohan, Vegeta, Piccolo]
        self.logic_modules = logic_modules  # Trade logics, DFS strategies, Ghost layers
        self.hyperbolic_chamber = hyperbolic_chamber  # Chamber scenarios
        self.history = []  # Track past battles

    def council_influence(self, logic, council_member):
        aggression_level = council_member.get_aggression_level()
        feedback = council_member.provide_feedback(logic)
        return feedback * aggression_level

    def simulate_battle(self):
        # Pull scenarios from Hyperbolic Chamber or logic modules
        if random.random() < 0.3:  # 30% chance to pull from Chamber
            participants = self.hyperbolic_chamber.select_scenarios(2)
        else:
            participants = random.sample(self.logic_modules, 2)

        ai_influences = random.sample(self.ai_council, 2)

        scores = []
        for i, logic in enumerate(participants):
            council_boost = self.council_influence(logic, ai_influences[i])
            base_score = logic.evaluate_performance()
            scores.append(base_score + council_boost)

        winner_idx = 0 if scores[0] >= scores[1] else 1
        loser_idx = 1 - winner_idx

        log_event("Conflict Arena", f"{participants[winner_idx].name} defeated {participants[loser_idx].name}. Scores: {scores}")

        # Adjust weights (survival bias tweaks)
        participants[winner_idx].adjust_weight(0.03 + random.uniform(0, 0.02))
        participants[loser_idx].adjust_weight(-0.03 + random.uniform(-0.02, 0))

        # Log historical battle
        self.history.append({
            "winner": participants[winner_idx].name,
            "loser": participants[loser_idx].name,
            "scores": scores
        })

        return self.history[-1]

    def run_cycle(self, cycles=5):
        results = []
        for _ in range(cycles):
            result = self.simulate_battle()
            results.append(result)
        log_event("Conflict Arena", f"Completed {cycles} battle cycles.")
        return results
