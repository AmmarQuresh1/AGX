"""
core.py

Main backend orchestrator for AGX.
- Initializes the backend. 
- Loads and validates the plan.
- Executes the plan if valid.
- Implements bounded retry with validation feedback.
- Prints final output messages.
"""
from pathlib import Path
from .compiler import compile_plan
from .planner import generate_plan
from .validate_plan import validate_plan
from typing import Optional

# Maximum number of retry attempts when validation fails
MAX_RETRIES = 3

# Returns to backend, always return a dict
def agx_main(prompt: Optional[str] = None, max_retries: int = MAX_RETRIES):
    if not prompt:
        print("[AGX] No prompt provided")
        return {"error": "no_prompt"}

    retry_count = 0
    validation_errors = []
    previous_plan = None
    
    while retry_count <= max_retries:
        if retry_count > 0:
            print(f"[AGX] Retry attempt {retry_count}/{max_retries}...")
        
        # Load plan using your planner
        plan = generate_plan(
            prompt=prompt,
            previous_plan=previous_plan if retry_count > 0 else None,
            validation_errors=validation_errors if retry_count > 0 else None
        )
        
        # Validate plan
        is_valid, errors = validate_plan(plan)
        
        if is_valid:
            print("[AGX] Compiling plan...")
            code = compile_plan(plan)
            
            if code:
                return {"code": code}
            else:
                print("[AGX] Compilation failed.")
                return {"error": "compilation_failed"}
        else:
            # Validation failed - store plan and errors for retry
            previous_plan = plan
            validation_errors = errors
            retry_count += 1
            
            if retry_count > max_retries:
                print(f"[AGX] Plan validation failed after {max_retries} retries - cannot compile.")
                return {"error": "validation_failed", "errors": errors, "retries_exhausted": True}
            
            # Continue to retry
            print(f"[AGX] Plan validation failed. Retrying with feedback...")