# === Reflexive Loop Core (Enhanced) ===

import random
import time
import threading
from data_intake import generate_metrics_from_data

# === SurgeCell Lite ===
def surgecell_allocate(task):
    load_factor = random.uniform(0.7, 1.0)
    print(f"[SurgeCell] Allocating resources to {task}. Load factor: {load_factor:.2f}")

# === Council AI Functions (Lite) ===
def goku_boost(weight):
    return weight * 1.05

def gohan_support(metrics):
    metrics['consistency'] *= 1.1
    return metrics

def vegeta_challenge(metrics):
    metrics['edge_discovery'] *= 1.15
    return metrics

def piccolo_harmonize(metrics):
    metrics['variance'] *= 0.9
    return metrics

# === Reflexive Functions ===
def adjust_aggression(profit):
    print(f"[Bankroll AI] Aggression adjusted based on profit: {profit:.2f}")

def register_logic(metrics):
    print(f"[Reflexive Deployment] Logic metrics registered.")

def evaluate_logic(metrics):
    score = metrics["profitability"] + metrics["sharpe_ratio"] - metrics["drawdown"]
    print(f"[Jarvis] Evaluation complete. Logic Score: {score:.2f}")
    return score

# === Reflexive Loop with Commands ===
class ReflexiveLoop:
    def __init__(self):
        self.metrics = {}
        self.running = True

  def generate_metrics(self):
    return generate_metrics_from_data()

    def loop(self):
        print("[Jarvis] Reflexive Loop Core Activated.")
        while self.running:
            surgecell_allocate("Reflexive Loop")
            self.metrics = self.generate_metrics()
            profit = self.metrics["profitability"]
            adjust_aggression(profit)
            register_logic(self.metrics)
            time.sleep(5)  # Delay for cycling

    def user_input(self):
        while self.running:
            cmd = input("\n[Jarvis] Awaiting Command (status / score / exit): ").strip().lower()
            if cmd == "status":
                print(f"[Jarvis] Current Metrics: {self.metrics}")
            elif cmd == "score":
                evaluate_logic(self.metrics)
            elif cmd == "exit":
                print("[Jarvis] Shutting down Reflexive Loop. Goodbye.")
                self.running = False
            else:
                print("[Jarvis] Unknown command. Try again.")

if __name__ == "__main__":
    rl = ReflexiveLoop()
    threading.Thread(target=rl.loop).start()
    rl.user_input()
