from .executor import run_plan
from .planner import generate_plan

def agx_main():
    print("[AGX] Backend initialized.")

    # Load plan using your planner
    plan = generate_plan()

    print("[AGX] Executing plan...")
    run_plan(plan)

