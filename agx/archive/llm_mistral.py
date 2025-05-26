import subprocess
import os

MISTRAL_CLI_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../tools/llama.cpp/build/bin/llama-cli")
)

MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../tools/llama.cpp/models/mistral-7b-instruct/mistral-7b-instruct-v0.2.Q5_K_M.gguf")
)

def generate_plan_from_mistral(task: str) -> str:
    with open("prompt_template.txt", "r") as f:
        template = f.read()

    prompt = f"[INST] {template.replace('{{TASK}}', task)} [/INST]"

    print("=== Final Prompt Sent to LLaMA ===")
    print(prompt)
    print("==================================")

    result = subprocess.run([
        MISTRAL_CLI_PATH,
        "-m", MODEL_PATH,
        "-p", prompt,
        "--n-predict", "256",
        "--temp", "0.0",
        "--top-k", "1",
        "--repeat-penalty", "1.2",
        "--no-conversation",
        "--json-schema", '{"type":"array","items":{"type":"object","required":["function","args"],"properties":{"function":{"type":"string","enum":["say_hello","log_message","add_numbers"]},"args":{"type":"object"}}}}'
    ], capture_output=True, text=True)


    print("=== STDOUT ===")
    print(result.stdout.strip())
    print("=== STDERR ===")
    print(result.stderr.strip())  # this shows loading errors or backend issues

    return result.stdout.strip()

