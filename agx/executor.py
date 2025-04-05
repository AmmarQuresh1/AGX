"""
Takes plan (JSON) in form:
[
  {"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "sum"},
  {"function": "log_message", "args": {"message": "{sum}"}}
]
"""

from .registry import registry

memory = {}  # Global memory for storing return values

def run_plan(plan):
    for step in plan:
        fn_name = step["function"]
        raw_args = step.get("args", {})
        assign_var = step.get("assign")

        resolved_args = {}
        for k, v in raw_args.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                var_name = v[1:-1]
                if var_name in memory:
                    resolved_args[k] = memory[var_name]
                else:
                    print(f"[AGX WARN] Variable '{var_name}' not found in memory. Using raw string '{v}'.")
                    resolved_args[k] = v
            else:
                resolved_args[k] = v

        print(f"[AGX EXEC] Running '{fn_name}' with args: {resolved_args}")

        if fn_name not in registry:
            print(f"[AGX ERROR] Function '{fn_name}' not registered!")
            continue

        try:
            result = registry[fn_name](**resolved_args)

            if assign_var and result is not None:
                memory[assign_var] = result
                print(f"[AGX MEM] Stored '{assign_var}' = {result}")

            if result is not None:
                memory["result"] = result

        except Exception as e:
            print(f"[AGX ERROR] Function '{fn_name}' raised an error: {e}")
