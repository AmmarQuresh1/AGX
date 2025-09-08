"""
devops_test.py

AWS-first demo registry.
Functions must match names referenced by the planner prompt.
"""
from __future__ import annotations
from agx.utils import _tf_label

# ----------------------
# Demo registry functions
# ----------------------

def log_message(message: str) -> None:
    """No-op logger for demo (prints)."""
    print(f"[AGX DEVOPS] {message}")


def set_bucket_name(name: str) -> str:
    """Return the provided name for deterministic reuse."""
    return name


def save_hcl_to_file(hcl_content: str, filename: str = "main.tf") -> str:
    """Saves the provided HCL content to a .tf file at repo root by default."""
    import os
    filepath = filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(hcl_content)
    return os.path.abspath(filepath)


def create_aws_s3_bucket(label: str, bucket_name: str) -> str:
        """Return Terraform HCL for an aws_s3_bucket."""
        return f'''
resource "aws_s3_bucket" "{label}" {{
    bucket = "{bucket_name}"

    tags = {{
        Name        = "{bucket_name}"
        Environment = "Dev"
        Owner       = "AGX"
    }}
}}
'''


def aws_s3_bucket_public_access_block(label: str, block_all_public: bool = True) -> str:
        """Return HCL for the aws_s3_bucket_public_access_block resource."""
        tf_bool = str(block_all_public).lower()
        return f'''
resource "aws_s3_bucket_public_access_block" "{label}" {{
    bucket = aws_s3_bucket.{label}.id

    block_public_acls       = {tf_bool}
    block_public_policy     = {tf_bool}
    ignore_public_acls      = {tf_bool}
    restrict_public_buckets = {tf_bool}
}}
'''


registry = {
    "log_message": log_message,
    "set_bucket_name": set_bucket_name,
    "create_aws_s3_bucket": create_aws_s3_bucket,
    "aws_s3_bucket_public_access_block": aws_s3_bucket_public_access_block,
    "save_hcl_to_file": save_hcl_to_file,
    "_tf_label": _tf_label
}
