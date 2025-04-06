import re

# Extensions for validate_plan:
# Detect "assign" wrongly inside args instead of at the top level.
# Warn about unused assigned variables.
# Detect unused or misspelled function names.
# Future-proof against circular references or duplicate assignments.

def validate_plan(plan):
    assigned_vars = set()
    errors = []

    for i, step in enumerate(plan):
        fn = step.get("function")
        args = step.get("args", {})
        assign = step.get("assign")

        # Check for placeholder references like "{var}"
        for k, v in args.items():
            if isinstance(v, str) and re.match(r"^{.*}$", v):
                var_name = v[1:-1]
                if var_name not in assigned_vars:
                    errors.append(f"[Plan Error] Step {i+1}: Variable '{var_name}' used in argument '{k}' before assignment.")

        # Register assigned variable for future references
        if assign:
            assigned_vars.add(assign)

    if errors:
        print("Plan validation failed:")
        for error in errors:
            print(error)
        return False

    print("Plan validation passed.")
    return True
