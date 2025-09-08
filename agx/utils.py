"""
agx/utils.py

Shared utility functions for the AGX package.
"""
import re

def _tf_label(name: str) -> str:
    """Terraform-safe resource label: letters, digits, underscores; must start with a letter or underscore."""
    import re
    label = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not (label and (label[0].isalpha() or label[0] == "_")):
        label = f"r_{label}"
    return label
