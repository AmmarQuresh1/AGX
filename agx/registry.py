def log_message(message, memory=None, final_messages=None):
    # Replace {var} with its value from memory, if available
    if isinstance(message, str):
        try:
            message = message.format(**memory)
        except KeyError as e:
            print(f"[AGX WARN] Variable '{e.args[0]}' not found in memory.")

    if final_messages is not None:
        final_messages.append(message)

    print(f"[AGX LOG] {message}")
    return None

def add_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError(f"add_numbers expected integers, got a={a} ({type(a)}), b={b} ({type(b)})")
    return a + b

def div_numbers(a, b):
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError(f"div_numbers expected integers, got a={a} ({type(a)}), b={b} ({type(b)})")
    return a / b

registry = {
    "log_message": log_message,
    "add_numbers": add_numbers,
    "div_numbers": div_numbers
}