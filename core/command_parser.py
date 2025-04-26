# command_parser.py

import re

def parse_command(command):
    """
    Parse the input command and return corresponding actions.
    """
    # Match "enhance my <task>"
    if re.match(r"enhance my (.*)", command):
        task = re.match(r"enhance my (.*)", command).group(1)
        return f"Enhancing {task}"
    
    # Match "build the <project>"
    elif re.match(r"build the (.*)", command):
        task = re.match(r"build the (.*)", command).group(1)
        return f"Building {task}"

    # For "optimize" command
    elif command == "optimize":
        return "Optimizing performance"
    
    # Default for unknown commands
    else:
        return "Unknown command"

# Example usage
if __name__ == "__main__":
    command = input("[Jarvis] Enter a command: ")
    result = parse_command(command)
    print(f"[Jarvis] Command result: {result}")
