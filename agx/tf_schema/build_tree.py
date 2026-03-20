"""
build_tree.py

Utility script to generate aws_resource_tree.json from raw Terraform provider
schema output (terraform providers schema -json).

Usage:
    terraform providers schema -json | python -m agx.tf_schema.build_tree
    python -m agx.tf_schema.build_tree schema.json

For MVP the checked-in aws_resource_tree.json is hand-curated.
This script exists for future automation when the provider schema is available.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Mapping from AWS service prefix to human-readable group description
GROUP_DESCRIPTIONS: dict[str, str] = {
    "s3": "Object storage buckets, objects, and access policies",
    "ec2": "Compute instances, AMIs, key pairs, volumes, and elastic IPs",
    "iam": "Identity and access management: roles, policies, users, and groups",
    "vpc": "Virtual private cloud: networks, subnets, gateways, and route tables",
    "lambda": "Serverless compute functions, layers, and permissions",
    "dynamodb": "NoSQL key-value and document database tables",
    "rds": "Relational database service instances and subnet groups",
    "sns": "Simple notification service topics and subscriptions",
    "sqs": "Simple queue service queues and policies",
    "cloudwatch": "Monitoring, logging, and alerting",
    "ecs": "Elastic container service clusters, services, and tasks",
    "eks": "Elastic Kubernetes service clusters and node groups",
    "elasticache": "In-memory caching with Redis and Memcached",
    "route53": "DNS management and health checks",
    "cloudfront": "Content delivery network distributions",
    "apigateway": "API Gateway REST and HTTP APIs",
    "kinesis": "Real-time data streaming",
    "secretsmanager": "Secrets management and rotation",
    "ssm": "Systems Manager parameters and documents",
    "kms": "Key management service encryption keys",
}

# Prefixes that map to non-obvious group names
PREFIX_OVERRIDES: dict[str, str] = {
    "aws_subnet": "vpc",
    "aws_security_group": "vpc",
    "aws_security_group_rule": "vpc",
    "aws_internet_gateway": "vpc",
    "aws_route_table": "vpc",
    "aws_route_table_association": "vpc",
    "aws_nat_gateway": "vpc",
    "aws_eip": "ec2",
    "aws_ebs_volume": "ec2",
    "aws_ami": "ec2",
    "aws_key_pair": "ec2",
    "aws_db_instance": "rds",
    "aws_db_subnet_group": "rds",
    "aws_db_parameter_group": "rds",
}


def _cty_to_simple(cty_type) -> str:
    """Convert a Terraform cty type to a simplified string."""
    if isinstance(cty_type, str):
        return cty_type
    if isinstance(cty_type, list):
        if cty_type[0] == "list":
            inner = _cty_to_simple(cty_type[1])
            return f"list({inner})"
        if cty_type[0] == "set":
            inner = _cty_to_simple(cty_type[1])
            return f"list({inner})"
        if cty_type[0] == "map":
            inner = _cty_to_simple(cty_type[1])
            return f"map({inner})"
        if cty_type[0] == "object":
            return "map(string)"
    return "string"


def _get_group(resource_type: str) -> str:
    """Determine the service group for a resource type."""
    if resource_type in PREFIX_OVERRIDES:
        return PREFIX_OVERRIDES[resource_type]
    # Strip aws_ prefix and take first segment
    name = resource_type.removeprefix("aws_")
    return name.split("_")[0]


def build_tree(raw_schema: dict) -> dict:
    """
    Parse raw ``terraform providers schema -json`` output into the compressed
    tree format used by AGX registry distillation.
    """
    tree: dict = {"provider": "aws", "service_groups": {}}

    # Navigate to the AWS provider resource schemas
    provider_schemas = raw_schema.get("provider_schemas", {})
    aws_schema = None
    for key, val in provider_schemas.items():
        if "aws" in key:
            aws_schema = val
            break
    if aws_schema is None:
        print("No AWS provider found in schema", file=sys.stderr)
        return tree

    resource_schemas = aws_schema.get("resource_schemas", {})

    for resource_type, schema in resource_schemas.items():
        if not resource_type.startswith("aws_"):
            continue

        group = _get_group(resource_type)
        if group not in GROUP_DESCRIPTIONS:
            continue  # Skip groups we haven't described yet

        block = schema.get("block", {})
        attrs = block.get("attributes", {})
        description = ""
        required_attrs: dict[str, str] = {}
        optional_attrs: dict[str, str] = {}

        for attr_name, attr_schema in attrs.items():
            # Skip computed-only attributes (outputs like id, arn)
            is_computed = attr_schema.get("computed", False)
            is_required = attr_schema.get("required", False)
            is_optional = attr_schema.get("optional", False)

            if is_computed and not is_required and not is_optional:
                continue

            simple_type = _cty_to_simple(attr_schema.get("type", "string"))

            if is_required:
                required_attrs[attr_name] = simple_type
            elif is_optional:
                optional_attrs[attr_name] = simple_type

        # Try to get description from schema
        desc = schema.get("description", "")
        if not desc:
            desc = f"Provides a {resource_type.removeprefix('aws_').replace('_', ' ')} resource"

        if group not in tree["service_groups"]:
            tree["service_groups"][group] = {
                "description": GROUP_DESCRIPTIONS.get(group, ""),
                "resources": {},
            }

        tree["service_groups"][group]["resources"][resource_type] = {
            "description": desc,
            "required_attrs": required_attrs,
            "optional_attrs": optional_attrs,
        }

    return tree


def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        raw = json.loads(path.read_text())
    else:
        raw = json.load(sys.stdin)

    tree = build_tree(raw)
    out_path = Path(__file__).parent / "aws_resource_tree.json"
    out_path.write_text(json.dumps(tree, indent=2) + "\n")
    count = sum(
        len(g["resources"]) for g in tree["service_groups"].values()
    )
    print(f"Wrote {count} resources across {len(tree['service_groups'])} groups to {out_path}")


if __name__ == "__main__":
    main()
