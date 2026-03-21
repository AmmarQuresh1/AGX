"""
utilities.py

Utility functions included in every dynamic registry.
These are general-purpose helpers that aren't tied to any specific AWS resource.
"""
from __future__ import annotations


def log_message(message: str) -> None:
    """Prints a message to stdout."""
    print(f"[AGX] {message}")


def save_hcl_to_file(hcl_content: str, filename: str = "main.tf") -> str:
    """Saves the provided HCL content to a .tf file. Returns the absolute path."""
    import os
    with open(filename, "w", encoding="utf-8") as f:
        f.write(hcl_content)
    return os.path.abspath(filename)


def sanitise_resource_name(name: str) -> str:
    """Terraform-safe resource label: letters, digits, underscores; must start with a letter or underscore."""
    import re
    label = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not (label and (label[0].isalpha() or label[0] == "_")):
        label = f"r_{label}"
    return label


def combine_hcl_blocks(blocks: list) -> str:
    """Joins any number of HCL blocks into one string separated by double newlines."""
    if isinstance(blocks, str):
        blocks = [blocks]
    return "\n\n".join(b.strip() for b in blocks if b and b.strip())


UTILITY_REGISTRY = {
    "log_message": log_message,
    "save_hcl_to_file": save_hcl_to_file,
    "sanitise_resource_name": sanitise_resource_name,
    "combine_hcl_blocks": combine_hcl_blocks,
}

UTILITY_SOURCE = {
    "log_message": '''def log_message(message: str) -> None:
    """Prints a message to stdout."""
    print(f"[AGX] {message}")''',

    "save_hcl_to_file": '''def save_hcl_to_file(hcl_content: str, filename: str = "main.tf") -> str:
    """Saves the provided HCL content to a .tf file. Returns the absolute path."""
    import os
    with open(filename, "w", encoding="utf-8") as f:
        f.write(hcl_content)
    return os.path.abspath(filename)''',

    "sanitise_resource_name": '''def sanitise_resource_name(name: str) -> str:
    """Terraform-safe resource label: letters, digits, underscores."""
    import re
    label = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not (label and (label[0].isalpha() or label[0] == "_")):
        label = f"r_{label}"
    return label''',

    "combine_hcl_blocks": '''def combine_hcl_blocks(blocks: list) -> str:
    """Joins any number of HCL blocks into one string separated by double newlines."""
    if isinstance(blocks, str):
        blocks = [blocks]
    return "\\n\\n".join(b.strip() for b in blocks if b and b.strip())''',
}
