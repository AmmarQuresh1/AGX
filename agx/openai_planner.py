from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

# Make sure you've set OPENAI_API_KEY in your .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_plan_from_openai(task: str) -> str:
    with open("o3-mini_prompt_template.txt", "r") as f:
        template = f.read()

    prompt = template.replace("{{TASK}}", task)

    print("=== Final Prompt Sent to GPT ===")
    print(prompt)
    print("================================")

    response = client.chat.completions.create(
        model="o3-mini-2025-01-31",  # or "gpt-3.5-turbo", or "o3-mini-2025-01-31" (if available to you)
        messages=[
            {"role": "user", "content": prompt}
        ],
        # temperature=0 # not usable with o3-mini
    )

    return response.choices[0].message.content
