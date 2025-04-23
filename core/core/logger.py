import datetime

def log_event(source, message):
    timestamp = datetime.datetime.now().isoformat()
    print(f"[LOG] {timestamp} | {source}: {message}")
    # Future: write to external log file or database