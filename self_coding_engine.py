# self_coding_engine.py

import os
import sys
import io
from surgecell_monitor import allocate_power
from savepoint_manager import save_state
from reflexive_loop import evaluate_logic

def self_code(command):
    if command.startswith("build "):
        module_name = command.replace("build ", "").strip()
        dir_path = "./self_coding"
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{module_name}.py")

        if module_name == "helper_tool":
            content = '''def generate_code_snippet(requirement):
    # Simulate generating code
    return f"# Code snippet for: {requirement}"

def refine_code_snippet(snippet):
    # Simulate refining code
    return snippet + "\\n# Refined for better efficiency"
'''
        else:
            content = f"# Auto-generated module: {module_name}\n"

        with open(file_path, "w") as f:
            f.write(content)
        print(f"[Self-Coder] Built new module: {module_name}.py")

    elif command.startswith("write "):
        try:
            _, module_name, code_line = command.split(" ", 2)
            file_path = f"./self_coding/{module_name}.py"
            with open(file_path, "a") as f:
                f.write(f"{code_line}\n")
            print(f"[Self-Coder] Wrote to {module_name}.py: {code_line}")
        except Exception as e:
            print(f"[Self-Coder] Error writing code: {e}")

    else:
        # Assume raw Python code with injected imports
        try:
            local_env = {}
            exec("from self_coding import helper_tool", globals(), local_env)  # Inject helper_tool
            
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            
            exec(command, globals(), local_env)  # Run in this enriched environment
            
            output = buffer.getvalue()
            sys.stdout = old_stdout
            print("[Self-Coder Output]:")
            print(output)
        except Exception as e:
            sys.stdout = old_stdout
            print(f"[Self-Coder] Code execution error: {e}")

def self_optimize():
    print("[Self-Optimizer] Optimization routine triggered (placeholder).")
