def say_hello(name):
    print(f"[AGX] Hello, {name} :)")
    return None  # still needs to return something

def log_message(message):
    print(f"[AGX LOG] {message}")
    return None

def add_numbers(a, b):
    return a + b  # now returns the result instead of printing

registry = {
    "say_hello": say_hello,
    "log_message": log_message,
    "add_numbers": add_numbers
}