"""
Takes plan (JSON) in form:
[
  {"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "sum"},
  {"function": "log_message", "args": {"message": "{sum}"}}
]

This file is responsible for executing each step in the plan,
substituting memory variables where needed,
and optionally storing return values for future use.
"""

from .registry import registry

memory = {}           # Global memory for storing intermediate results
final_messages = []   # Optional: final output collector

def resolve_variables(value, memory):
    if isinstance(value, str):
        try:
            return value.format(**memory)
        except KeyError as e:
            print(f"\033[93m[AGX WARN] Missing memory variable: {e.args[0]} in '{value}'\033[93m")
            return value
    elif isinstance(value, dict):
        return {k: resolve_variables(v, memory) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_variables(item, memory) for item in value]
    else:
        return value

def run_plan(plan):
    for step in plan:
        fn_name = step["function"]
        raw_args = step.get("args", {})
        assign_var = step.get("assign")

        # Resolve any {placeholders} in arguments
        resolved_args = resolve_variables(raw_args, memory)

        print(f"[AGX EXEC] Running '{fn_name}' with args: {resolved_args}")

        if fn_name not in registry:
            print(f"\033[0m[AGX ERROR] Function '{fn_name}' not registered!\033[0m")
            continue

        try:
            if fn_name == "log_message":
                # Inject memory and final message collector only into log_message
                result = registry[fn_name](**resolved_args, memory=memory, final_messages=final_messages)
            else:
                result = registry[fn_name](**resolved_args)

            # Save result to memory if "assign" is specified
            if assign_var and result is not None:
                memory[assign_var] = result
                print(f"[AGX MEM] Stored '{assign_var}' = {result}")

            if result is not None:
                memory["result"] = result

        except Exception as e:
            print(f"\033[0m[AGX ERROR] Function '{fn_name}' raised an error: {e}\033[0m")

