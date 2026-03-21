"""
planner.py

Generates a plan based on user input.
- Uses AI backend to generate raw JSON output.
- Extracts and validates the first JSON array from the output.
- Returns a list of steps (function and args from JSON) or an empty list if invalid.
"""

from .llm_openai import generate_raw_json
from typing import Optional
import json
import re


def _extract_json_array(text: str) -> Optional[str]:
    """
    Extract the first top-level JSON array from *text* using a state machine
    that correctly handles nested braces/brackets inside string values and
    escape sequences.  Returns the raw JSON string or None if not found.
    """
    i = 0
    n = len(text)
    # Find the opening '[' of the first array
    while i < n and text[i] != '[':
        i += 1
    if i >= n:
        return None

    start = i
    depth = 0       # bracket depth ([ and ])
    in_string = False
    escape = False

    while i < n:
        ch = text[i]

        if escape:
            escape = False
            i += 1
            continue

        if ch == '\\' and in_string:
            escape = True
            i += 1
            continue

        if ch == '"':
            in_string = not in_string
            i += 1
            continue

        if not in_string:
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]

        i += 1

    return None  # unbalanced / not found

def generate_plan(prompt=None, previous_plan=None, validation_errors=None, prompt_fragment: Optional[str] = None):
    # Interactively prompts user if no input is provided
    if not prompt:
        prompt = input("[AGX] What would you like to do? ")

    print("[AGX Planner] Generating plan...")
    raw_output = generate_raw_json(
        prompt,
        previous_plan=previous_plan,
        validation_errors=validation_errors,
        prompt_fragment=prompt_fragment,
    )

    print("=== RAW AI OUTPUT ===")
    print(raw_output)
    print("========================")

    # Extract the first valid JSON array using bracket-balanced state machine
    raw_json = _extract_json_array(raw_output)
    if not raw_json:
        print("[AGX Planner] Failed to extract JSON.")
        return []
    try:
        plan = json.loads(raw_json)
        print("[AGX Planner] Plan parsed successfully.")
        return plan
    except json.JSONDecodeError as e:
        print("[AGX Planner] JSON parsing error:", e)
        return []
