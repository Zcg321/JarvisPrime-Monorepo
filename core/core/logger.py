import datetime

def log_event(source, message): timestamp = datetime.datetime.now().isoformat() log_entry = f"[{timestamp}] [{source}] {message}\n" # Save to log file for mobile visibility with open("jarvis_logs.txt", "a") as log_file: log_file.write(log_entry)

