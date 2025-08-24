import threading
from core.reflexive_loop import ReflexiveLoop, evaluate_logic
from core.surgecell_monitor import allocate_power
from core.savepoint_manager import save_state, load_state
from self_coding_engine import self_code, self_optimize  # Self-coding imports

rl = ReflexiveLoop()
auto_loop_thread = None  # Thread placeholder

def auto_evolve_loop():
    while rl.running:
        print("\n[Jarvis] Auto-Evolution Cycle Triggered...")
        metrics = rl.generate_metrics()
        print(f"[Jarvis] Metrics Generated: {metrics}")
        score = evaluate_logic(metrics)
        save_state(metrics)
        print(f"[Jarvis] Logic Score: {score:.2f}")
        rl.sleep_cycle(10)  # Sleep between cycles

def jarvis_mvi_menu():
    global auto_loop_thread
    while True:
        print("\n=== Jarvis Prime MVI Menu ===")
        print("1. Status Check")
        print("2. Trigger Evolution (Manual)")
        print("3. Rollback to Savepoint")
        print("4. Exit")
        print("5. Start Auto-Evolution Loop")
        print("6. Stop Auto-Evolution Loop")
        print("7. Self-Code Command")  # Added Self-Code option

        choice = input("Select an option: ").strip()

        if choice == "1":
            allocate_power("Reflexive Loop", "normal")

        elif choice == "2":
            print("[Jarvis] Triggering Reflexive Evolution...")
            metrics = rl.generate_metrics()
            print(f"[Jarvis] Metrics Generated: {metrics}")
            score = evaluate_logic(metrics)
            save_state(metrics)
            print(f"[Jarvis] Logic Score: {score:.2f}")

        elif choice == "3":
            print("[Jarvis] Rolling back to last savepoint...")
            metrics = load_state()
            if metrics:
                print(f"[Jarvis] Restored Metrics: {metrics}")
                score = evaluate_logic(metrics)
                print(f"[Jarvis] Logic Score (Restored): {score:.2f}")

        elif choice == "4":
            if rl.running:
                rl.running = False
                if auto_loop_thread:
                    auto_loop_thread.join()
            print("[Jarvis] Exiting MVI Core. Goodbye.")
            break

        elif choice == "5":
            if not rl.running:
                rl.running = True
                auto_loop_thread = threading.Thread(target=auto_evolve_loop)
                auto_loop_thread.start()
                print("[Jarvis] Auto-Evolution Loop started.")
            else:
                print("[Jarvis] Auto-Evolution already running.")

        elif choice == "6":
            if rl.running:
                rl.running = False
                if auto_loop_thread:
                    auto_loop_thread.join()
                print("[Jarvis] Auto-Evolution Loop stopped.")
            else:
                print("[Jarvis] Auto-Evolution not running.")

        elif choice == "7":
            command = input("[Jarvis] Enter Self-Code Command: ").strip()
            self_code(command)

        else:
            print("[Jarvis] Invalid choice. Try again.")

if __name__ == "__main__":
    jarvis_mvi_menu()
