def say_hello(name):
    print(f"[AGX] Hello, {name} :)")
    return None  # still needs to return something

def log_message(message):
    print(f"[AGX LOG] {message}")
    return None

def add_numbers(a, b):
    if not isinstance(a, int) or not isinstance(b, int):
        raise ValueError(f"add_numbers expected integers, got a={a} ({type(a)}), b={b} ({type(b)})")
    return a + b

registry = {
    "say_hello": say_hello,
    "log_message": log_message,
    "add_numbers": add_numbers
}