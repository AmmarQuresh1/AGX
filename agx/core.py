"""
core.py

Main backend orchestrator for AGX.
- Initializes the backend. 
- Loads and validates the plan.
- Executes the plan if valid.
- Prints final output messages.
"""
from pathlib import Path
from .compiler import compile_plan
from .planner import generate_plan
from .validate_plan import validate_plan
from typing import Optional

def agx_main(prompt: Optional[str] = None):
    print("[AGX] Backend initialized.")

    # Load plan using your planner
    plan = generate_plan(prompt=prompt)

    if validate_plan(plan):
        print("[AGX] Compiling plan...")
        generate_code = compile_plan(plan)

        if generate_code:
            return generate_code
        else:
            print("[AGX] Compilation failed.")
            return None
    else:
        print("[AGX] Plan validation failed - cannot compile.")
        return None