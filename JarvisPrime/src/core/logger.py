import datetime
import os

# Log event with levels and rotation
def log_event(source, message, level="INFO"):
    timestamp = datetime.datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] [{source}] {message}\n"
    
    # Daily log rotation
    log_filename = f"jarvis_logs_{datetime.datetime.now().date()}.txt"
    
    # Save to log file
    with open(log_filename, "a") as log_file:
        log_file.write(log_entry)
    
    # Console mirroring for mobile visibility
    print(log_entry.strip())

    # Future: Memory hook to Tool-Builder AI for log parsing

# Example usage:
# log_event("Goku Engine", "Boost activated", level="INFO")
# log_event("DFF Scraper", "CSV link not found", level="WARNING")
# log_event("Bankroll AI", "Failed bankroll adjustment", level="ERROR")
