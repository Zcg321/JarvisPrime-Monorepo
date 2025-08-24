# === self_evolution.py ===

class SelfEvaluator:
    def __init__(self):
        self.performance_history = []
        self.improvement_factor = 0.1  # Starting learning rate

    def evaluate_performance(self, task_name, result_score, target_score):
        score = (result_score / target_score) * 100
        self.performance_history.append({
            "task": task_name,
            "score": score
        })
        print(f"[Self-Evaluation] Task '{task_name}' Performance Score: {score:.2f}%")
        return score

    def analyze_performance(self):
        avg_score = sum(entry["score"] for entry in self.performance_history) / len(self.performance_history)
        print(f"[Self-Evaluation] Average Performance: {avg_score:.2f}%")
        return avg_score

    def adjust_for_improvement(self, avg_score):
        if avg_score >= 90:
            self.improvement_factor *= 0.9
        else:
            self.improvement_factor *= 1.1
        print(f"[Self-Evaluation] Adjusted Improvement Factor: {self.improvement_factor:.4f}")

class SelfOptimizer:
    def __init__(self):
        self.weights = {
            "goku": 1.05,
            "gohan": 1.10,
            "vegeta": 1.15,
            "piccolo": 0.90
        }

    def adjust_weights_based_on_performance(self, performance_score, improvement_factor):
        adjustment_factor = (performance_score / 100) * improvement_factor
        self.weights['goku'] += adjustment_factor
        self.weights['piccolo'] -= adjustment_factor
        print(f"[Self-Optimization] Adjusted Weights: {self.weights}")

class JarvisSelfEvolution:
    def __init__(self):
        self.evaluator = SelfEvaluator()
        self.optimizer = SelfOptimizer()

    def run_task(self, task_name, result_score, target_score):
        performance_score = self.evaluator.evaluate_performance(task_name, result_score, target_score)
        avg_score = self.evaluator.analyze_performance()
        self.evaluator.adjust_for_improvement(avg_score)
        self.optimizer.adjust_weights_based_on_performance(performance_score, self.evaluator.improvement_factor)
        return self.optimizer.weights
