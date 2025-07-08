"""
devops_test.py

DevOps automation registry for deployment and infrastructure management.
Demo functions for AWS operations.
Keep imports inside functions or adjust the compiler.
"""

def log_message(message: str) -> None:
    print(f"[AGX DEVOPS] {message}")

def set_bucket_name(name: str) -> str:
    return name

def save_hcl_to_file(hcl_content: str, filename: str = "main.tf") -> str:
    """Saves the provided HCL content to a .tf file."""
    import os
    output_dir = "infrastructure"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        f.write(hcl_content)
    
    return f"Successfully saved configuration to {filepath}"

def create_aws_s3_bucket(bucket_name: str) -> str:
    """
    Generate HCL code for a S3 bucket.
    """
    return f'''
resource "aws_s3_bucket" "{bucket_name}" {{
  bucket = "{bucket_name}"

  tags = {{
    Name        = "{bucket_name}"
    Environment = "Dev"
    Owner = "AGX"
  }}
}}
'''

def aws_s3_bucket_public_access_block(bucket_name: str, block_all_public: bool = True) -> str:
    return f'''
resource "aws_s3_bucket_public_access_block" "{bucket_name}" {{
  bucket = aws_s3_bucket.{bucket_name}.id

  block_public_acls       = {block_all_public}
  block_public_policy     = {block_all_public}
  ignore_public_acls      = {block_all_public}
  restrict_public_buckets = {block_all_public}
}}
'''



registry = {
    "log_message": log_message,
    "set_bucket_name": set_bucket_name,
    "save_hcl_to_file": save_hcl_to_file,
    "create_aws_s3_bucket": create_aws_s3_bucket,
    "aws_s3_bucket_public_access_block": aws_s3_bucket_public_access_block,
}