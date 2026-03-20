"""Tests for registry distillation (2-pass LLM pruning)."""
import json
from agx.distill import (
    load_resource_tree,
    get_group_summaries,
    get_resources_for_groups,
    distill_registry,
)


def test_load_resource_tree():
    tree = load_resource_tree()
    assert tree["provider"] == "aws"
    assert "s3" in tree["service_groups"]


def test_get_group_summaries():
    tree = load_resource_tree()
    summaries = get_group_summaries(tree)
    assert len(summaries) > 0
    names = [s["name"] for s in summaries]
    assert "s3" in names
    assert "ec2" in names


def test_get_resources_for_groups():
    tree = load_resource_tree()
    resources = get_resources_for_groups(tree, ["s3"])
    types = [r["type"] for r in resources]
    assert "aws_s3_bucket" in types
    assert any(r["type"] == "aws_s3_bucket" for r in resources)


def test_get_resources_for_invalid_group():
    tree = load_resource_tree()
    resources = get_resources_for_groups(tree, ["nonexistent"])
    assert resources == []


def test_pass1_selects_relevant_groups():
    """Mock LLM returning s3 group then s3 bucket resource."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["s3"]'
        return '["aws_s3_bucket"]'

    result = distill_registry("Create an S3 bucket named test", mock_llm)
    assert result["error"] is None
    assert "aws_s3_bucket" in result["resources"]


def test_pass2_selects_resources():
    """Mock LLM returning specific resources."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["s3"]'
        return '["aws_s3_bucket", "aws_s3_bucket_public_access_block"]'

    result = distill_registry("Create a private S3 bucket", mock_llm)
    assert result["error"] is None
    assert "aws_s3_bucket" in result["resources"]
    assert "aws_s3_bucket_public_access_block" in result["resources"]


def test_empty_pass1_returns_error():
    """Non-infra prompt should return empty groups → error."""
    def mock_llm(prompt):
        return '[]'

    result = distill_registry("What is Terraform?", mock_llm)
    assert result["resources"] is None
    assert "non-infrastructure" in result["error"].lower() or "no relevant" in result["error"].lower()


def test_too_many_resources_returns_error():
    """If LLM selects >20 resources, should error."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["s3", "ec2", "iam", "vpc", "lambda", "dynamodb", "rds", "sns", "sqs", "cloudwatch"]'
        # Return way too many resources
        return json.dumps([f"aws_fake_{i}" for i in range(25)])

    result = distill_registry("Create everything", mock_llm)
    assert result["resources"] is None
    assert "narrow" in result["error"].lower() or "max" in result["error"].lower()


def test_empty_pass2_returns_error():
    """If LLM returns no specific resources, should error."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["s3"]'
        return '[]'

    result = distill_registry("Something vague", mock_llm)
    assert result["resources"] is None
    assert result["error"] is not None


def test_end_to_end_distillation():
    """Full 2-pass with VPC resources."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["vpc"]'
        return '["aws_vpc", "aws_subnet", "aws_internet_gateway"]'

    result = distill_registry("Create a VPC with a public subnet", mock_llm)
    assert result["error"] is None
    assert "aws_vpc" in result["resources"]
    assert "aws_subnet" in result["resources"]
    assert "aws_internet_gateway" in result["resources"]
    assert call_count == 2


def test_auto_includes_transitive_deps():
    """Lambda depends on IAM role — should be auto-included even if LLM doesn't select it."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["lambda"]'
        # LLM only selects lambda_function, not iam_role
        return '["aws_lambda_function"]'

    result = distill_registry("Deploy a Lambda function", mock_llm)
    assert result["error"] is None
    # Lambda was selected by LLM
    assert "aws_lambda_function" in result["resources"]
    # IAM role should be auto-included via dependency resolution
    assert "aws_iam_role" in result["resources"]


def test_auto_includes_deep_transitive_deps():
    """aws_instance → aws_subnet → aws_vpc — deep chain should be fully resolved."""
    call_count = 0
    def mock_llm(prompt):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return '["ec2"]'
        return '["aws_instance"]'

    result = distill_registry("Launch an EC2 instance", mock_llm)
    assert result["error"] is None
    assert "aws_instance" in result["resources"]
    # Transitive deps: instance → subnet → vpc, instance → security_group → vpc
    assert "aws_subnet" in result["resources"]
    assert "aws_security_group" in result["resources"]
    assert "aws_vpc" in result["resources"]
