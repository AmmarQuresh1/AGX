"""
llm_openai.py

Calls openAI api to generate an output from prompt.
- Prompts are in prompt_templates subfolder.
- The prompts are usually requesting for output in JSON that gets parsed by planner.py.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import json
import re
from typing import Optional

try:  # pragma: no cover - just setup logic
    from openai import OpenAI  # type: ignore
except Exception:  # openai might not be installed
    OpenAI = None  # type: ignore

load_dotenv()

# Only create a client if openai is available and an API key is provided
_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=_api_key) if OpenAI and _api_key else None

def _build_dynamic_template(prompt_fragment: str) -> str:
    """Build a planner prompt template from a dynamic function listing."""
    return """Instruction: {{TASK}}

{{PREVIOUS_PLAN_WITH_ERRORS}}

If the instruction is NOT an infrastructure request (e.g. a question, conversational message, or unsafe request), return ONLY a single log_message step explaining why. Otherwise, generate the full plan.

Variable assignment and reuse:
- No implicit function calls such as using a function name inside a variable
- To reuse a value produced earlier, first capture it with "assign", then reference it as a string value like "{varName}" in later args.
- Only reference variables that were previously assigned. Do not invent variables like "{previous_result}".
- The assign key is top-level only and must not appear inside args.

Step object schema (verbal form):
- function: string. Must exactly match one of the allowed function names listed below.
- args: object. The named parameters for the function.
- assign: optional string. Top-level only (never inside args). Use only when capturing a return value for reuse.

Available functions (names must match runtime):
""" + prompt_fragment + """

Using available functions, respond only with JSON plan with form as shown below with no additions(no newline characters etc):
[
  {
    // Step 1: Set a value for reuse
    "function": "<function_name>",
    "args": { "param": "<value>" },
    "assign": "<var>"
  },
  {
    // Step 2: Use assigned variable in another function
    "function": "<function_name>",
    "args": { "param": "{<var>}" },
    "assign": "<var>"
  }
]
"""


def generate_raw_json(task: str, previous_plan: Optional[list] = None, validation_errors: Optional[list[str]] = None, prompt_fragment: Optional[str] = None) -> str:
    if client is None:
        raise RuntimeError(
            "OpenAI client is not configured. Install the openai package and set OPENAI_API_KEY."
        )

    if prompt_fragment:
        # Use dynamic template built from distilled registry
        template = _build_dynamic_template(prompt_fragment)
    else:
        # Fall back to static template
        current_dir = Path(__file__).parent
        template_path = current_dir / "prompt_templates" / "devops_test.txt"
        with open(template_path, "r") as f:
            template = f.read()

    # Replace task placeholder
    prompt = template.replace("{{TASK}}", task)
    
    # Handle previous plan with validation errors if provided
    if previous_plan and validation_errors and len(validation_errors) > 0:
        # Parse validation errors to extract step numbers
        # Errors are formatted as: "[Plan Error] Step N: ..."
        step_errors = {}
        for error in validation_errors:
            match = re.search(r"Step (\d+):", error)
            if match:
                step_num = int(match.group(1)) - 1  # Convert to 0-based index
                if step_num not in step_errors:
                    step_errors[step_num] = []
                # Extract just the error message part (after "Step N: ")
                error_msg = error.split(":", 1)[1].strip() if ":" in error else error
                step_errors[step_num].append(error_msg)
        
        # Format the previous plan as JSON with error annotations
        plan_json = json.dumps(previous_plan, indent=2)
        
        # Add error annotations to the JSON
        # We'll add comments after the closing brace of steps that have errors
        annotated_lines = []
        lines = plan_json.split('\n')
        current_step = -1
        in_step = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect step boundaries (lines starting with '{')
            if stripped.startswith('{') and not in_step:
                current_step += 1
                in_step = True
            
            annotated_lines.append(line)
            
            # If this step has errors and we're closing the step object, add error comment
            if stripped == '}' and in_step and current_step in step_errors:
                # Get the indentation of the closing brace
                indent = len(line) - len(line.lstrip())
                # Add error comment with same indentation
                error_messages = '; '.join(step_errors[current_step])
                error_comment = ' ' * indent + f'  // ERROR: {error_messages}'
                annotated_lines.append(error_comment)
                in_step = False
            elif stripped == '}' and in_step:
                in_step = False
        
        annotated_plan = '\n'.join(annotated_lines)
        
        # Create formatted text
        errors_text = "Previous plan that failed validation:\n\n"
        errors_text += annotated_plan
        errors_text += "\n\nPlease fix the above plan by addressing the validation errors marked with // ERROR comments."
        
        prompt = prompt.replace("{{PREVIOUS_PLAN_WITH_ERRORS}}", errors_text)
    else:
        # Remove previous plan section if no previous plan (first attempt)
        prompt = prompt.replace("{{PREVIOUS_PLAN_WITH_ERRORS}}", "")

    print("Prompt Sent to GPT")

    response = client.responses.create(
        model="gpt-5.4-2026-03-17",  # full GPT-5.4 — best for structured plan generation
        input=prompt,
    )

    return response.output_text


def call_llm(prompt: str) -> str:
    """
    Generic LLM call for non-planning uses (e.g. registry distillation).
    Takes a prompt string, returns raw output text.
    """
    if client is None:
        raise RuntimeError(
            "OpenAI client is not configured. Install the openai package and set OPENAI_API_KEY."
        )

    response = client.responses.create(
        model="gpt-4.1-mini-2025-04-14",
        input=prompt,
        temperature=0,
    )

    return response.output_text
