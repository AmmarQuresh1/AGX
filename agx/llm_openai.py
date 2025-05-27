"""
llm_openai.py

Calls openAI api to generate an output from prompt:
- Prompts are in prompt_templates subfolder.
- The prompts are usually requesting for output in JSON that gets parsed by planner.py.
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

# Make sure you've set OPENAI_API_KEY in your .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_raw_json(task: str) -> str:
    with open("prompt_templates/o3-mini_prompt_template.txt", "r") as f:
        template = f.read()

    prompt = template.replace("{{TASK}}", task)

    print("=== Prompt Sent to GPT ===")
    print(prompt)
    print("================================")

    response = client.chat.completions.create(
        model="gpt-4.1-nano-2025-04-14",  # or"o3-mini-2025-01-31" or "gpt-4o-2024-08-06"
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0 # not usable with o3-mini
    )

    return response.choices[0].message.content
