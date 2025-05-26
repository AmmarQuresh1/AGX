"""
core.py

Main backend orchestrator for AGX.
- Initializes the backend. 
- Loads and validates the plan.
- Executes the plan if valid.
- Prints final output messages.
"""
from .executor import run_plan, final_messages 
from .planner import generate_plan
from .validate_plan import validate_plan

def agx_main():
    print("[AGX] Backend initialized.")

    # Load plan using your planner
    plan = generate_plan()

    if validate_plan(plan):
        print("[AGX] Executing plan...")
        run_plan(plan)

    if final_messages:
        print("\n[AGX FINAL OUTPUT]")
        for msg in final_messages:
            print(f"- {msg}")

