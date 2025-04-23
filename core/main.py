from dfs_optimizer import optimize_lineup from trade_scoring_engine import score_trade, post_trade_review from logger import log_event

def view_logs(): try: with open("jarvis_logs.txt", "r") as file: logs = file.read() print(logs) except FileNotFoundError: print("No logs found.")

def jarvis_menu(): print("=== Jarvis Prime Menu ===") print("1. Run DFS Optimizer") print("2. Run Trade Scoring (Batch 5 Trades)") print("3. View Logs")

choice = input("Select an option: ")

if choice == "1":
    optimize_lineup()
elif choice == "2":
    trades = [score_trade({}) for _ in range(5)]
    post_trade_review(trades)
elif choice == "3":
    view_logs()
else:
    print("Invalid choice.")

if name == "main": jarvis_menu()

