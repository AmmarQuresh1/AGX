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
            # Save the generated code to downloads folder (cross-platform)
            # downloads_dir = Path.home() / "Downloads"
            # output_file = downloads_dir / "generated_plan.py"
            
            # with open(output_file, "w") as f:
            #     f.write(generate_code)
            # REDUNDANT
            print("[AGX] Plan compiled successfully! Check generated_plan.py")
            print("[AGX] Run with: python generated_plan.py")
            return generate_code
        else:
            print("[AGX] Compilation failed.")
            return None
    else:
        print("[AGX] Plan validation failed - cannot compile.")
        return None