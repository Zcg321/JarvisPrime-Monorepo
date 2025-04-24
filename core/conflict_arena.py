from logger import log_event
import random

class ConflictArena:
    def __init__(self, ai_council, logic_modules, hyperbolic_chamber, sentiment_tracker):
        self.ai_council = ai_council
        self.logic_modules = logic_modules
        self.hyperbolic_chamber = hyperbolic_chamber
        self.sentiment_tracker = sentiment_tracker
        self.history = []

    def council_influence(self, logic, council_member):
        aggression_level = council_member.get_aggression_level()
        feedback = council_member.provide_feedback(logic)
        sentiment_adjustment = self.sentiment_tracker.get_divergence_factor()
        total_feedback = feedback * aggression_level * (1.0 + sentiment_adjustment)
        return total_feedback

    def simulate_battle(self):
        participants = (
            self.hyperbolic_chamber.select_scenarios(2)
            if random.random() < 0.3 else random.sample(self.logic_modules, 2)
        )
        ai_influences = random.sample(self.ai_council, 2)

        scores = []
        for i, logic in enumerate(participants):
            council_boost = self.council_influence(logic, ai_influences[i])
            base_score = logic.evaluate_performance()
            scores.append(base_score + council_boost)

        winner_idx = 0 if scores[0] >= scores[1] else 1
        loser_idx = 1 - winner_idx

        log_event("Conflict Arena", f"{participants[winner_idx].name} defeated {participants[loser_idx].name}. Scores: {scores}")

        # Ripple/Noise applied to weight adjustments
        self.adjust_survival_bias(participants[winner_idx], winner=True)
        self.adjust_survival_bias(participants[loser_idx], winner=False)

        self.history.append({
            "winner": participants[winner_idx].name,
            "loser": participants[loser_idx].name,
            "scores": scores
        })

        # Override loop: Detect repetitive matchups
        if self.detect_stagnation():
            log_event("Conflict Arena", "Override triggered: Rebalancing council weights due to repetitive outcomes.")

        return self.history[-1]

    def adjust_survival_bias(self, logic, winner=True):
        base_adjustment = 0.03 if winner else -0.03
        ripple = random.uniform(-0.02, 0.02)
        final_adjustment = base_adjustment + ripple
        logic.adjust_weight(final_adjustment)

    def detect_stagnation(self):
        if len(self.history) < 5:
            return False
        last_five = [entry["winner"] for entry in self.history[-5:]]
        return len(set(last_five)) == 1  # Stagnation if same winner

    def run_cycle(self, cycles=5):
        results = []
        for _ in range(cycles):
            result = self.simulate_battle()
            results.append(result)
        log_event("Conflict Arena", f"Completed {cycles} battle cycles.")
        return results
