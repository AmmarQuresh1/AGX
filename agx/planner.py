from .mistral_planner import generate_plan_from_mistral
import json
import re

def generate_plan(user_input=None):
    if not user_input:
        user_input = input("[AGX] What would you like to do? ")

    print("[AGX Planner] Generating plan...")
    raw_output = generate_plan_from_mistral(user_input)

    print("=== RAW LLaMA OUTPUT ===")
    print(raw_output)
    print("========================")

    # ✅ Extract the first valid JSON array using regex
    match = re.search(r"\[\s*{.*?}\s*\]", raw_output, re.DOTALL)
    if not match:
        print("[AGX Planner] Failed to extract JSON.")
        return []

    try:
        plan = json.loads(match.group(0))
        for step in plan:
            if step["function"] == "name_of_function":
                print("[AGX Planner] Invalid dummy function detected. Ignoring plan.")
                return []
        print("[AGX Planner] Plan parsed successfully.")
        return plan
    except json.JSONDecodeError as e:
        print("[AGX Planner] JSON parsing error:", e)
        return []

    