# === Reflexive Loop Core (Enhanced) ===

import random
import time
import threading
from data_intake import generate_metrics_from_data
from reflex_chain_handler_final import trigger_reflex_chain  # Trigger chain logic here
from core.surgecell_monitor import allocate_power

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

    def sleep_cycle(self, seconds):
        time.sleep(seconds)

    def generate_metrics(self):
        return generate_metrics_from_data()

    def loop(self):
        print("[Jarvis] Reflexive Loop Core Activated.")
        while self.running:
            allocate_power("Reflexive Loop", "normal")  # SurgeCell status
            self.metrics = self.generate_metrics()
            score = evaluate_logic(self.metrics)  # Evaluate before Council tweaks
            self.metrics = trigger_reflex_chain("Reflexive Loop", ["goku", "gohan", "vegeta", "piccolo"])  # Call reflex chain handler
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
