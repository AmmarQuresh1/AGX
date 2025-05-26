"""
validate_plan.py

Checks JSON plans for correctness before execution.
- An argument can't use a variable before it is assigned.
- More validation checks will be added in the future.
"""
import re

# Extensions for validate_plan:
# Only valid function names can be used (HIGH PRIORITY)
# Detect "assign" wrongly inside args instead of at the top level.
# Warn about unused assigned variables.
# Detect unused or misspelled function names.
# Future-proof against circular references or duplicate assignments.

def validate_plan(plan):
    assigned_vars = set()  # Keeps track of all variables that get assigned values
    errors = []            # Collects any validation errors found

    for i, step in enumerate(plan):
        fn = step.get("function")
        args = step.get("args", {})
        assign = step.get("assign")

        # Check if any arguments reference variables (format: {variable_name})
        for k, v in args.items():
            if isinstance(v, str) and re.match(r"^{.*}$", v): 
                var_name = v[1:-1] # Remove the curly braces
                if var_name not in assigned_vars: 
                    errors.append(f"[Plan Error] Step {i+1}: Variable '{var_name}' used in argument '{k}' before assignment.")

        # Track this step's assigned variable for future steps
        if assign:
            assigned_vars.add(assign)

    if errors:
        print("Plan validation failed:")
        for error in errors:
            print(error)
        return False

    print("Plan validation passed.")
    return True
