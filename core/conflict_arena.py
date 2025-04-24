# Conflict Arena (Adaptive Survival Simulator)
from logger import log_event
import random

class ConflictArena:
    def __init__(self, ai_council, logic_modules):
        self.ai_council = ai_council  # [Goku, Gohan, Vegeta, Piccolo]
        self.logic_modules = logic_modules  # Trade logics, DFS strategies, Ghost layers

    def simulate_battle(self):
        participants = random.sample(self.logic_modules, 2)
        ai_influences = random.sample(self.ai_council, 2)

        # Apply council influences to participants
        scores = []
        for i, logic in enumerate(participants):
            council_boost = ai_influences[i].provide_feedback(logic)
            base_score = logic.evaluate_performance()
            scores.append(base_score + council_boost)

        # Determine winner/loser
        winner_idx = 0 if scores[0] >= scores[1] else 1
        loser_idx = 1 - winner_idx

        log_event("Conflict Arena", f"{participants[winner_idx].name} defeated {participants[loser_idx].name}. Scores: {scores}")

        # Adjust survival odds, feed into reflexive system
        participants[winner_idx].adjust_weight(0.05)  # Winner gets stronger
        participants[loser_idx].adjust_weight(-0.05)  # Loser penalized

        return {
            "winner": participants[winner_idx].name,
            "loser": participants[loser_idx].name,
            "scores": scores
        }

    def run_cycle(self, cycles=5):
        results = []
        for _ in range(cycles):
            result = self.simulate_battle()
            results.append(result)
        log_event("Conflict Arena", f"Completed {cycles} battle cycles.")
        return results
