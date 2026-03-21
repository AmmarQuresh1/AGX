"""
Tests for agx/planner.py — specifically the _extract_json_array state-machine parser.
No network calls are made; generate_raw_json is monkeypatched.
"""
import json
import pytest
from unittest.mock import patch

from agx.planner import _extract_json_array, generate_plan


# ---------------------------------------------------------------------------
# _extract_json_array unit tests
# ---------------------------------------------------------------------------

def test_simple_json_array():
    """Basic single-step plan with no nested braces."""
    raw = '[{"function": "log_message", "args": {"message": "hello"}}]'
    result = _extract_json_array(raw)
    assert result is not None
    parsed = json.loads(result)
    assert parsed[0]["function"] == "log_message"


def test_nested_braces_inside_string():
    """
    IAM/Lambda case: a string value itself contains { } characters.
    The old regex r'\\[\\s*{.*?}\\s*\\]' would stop at the first } and break.
    """
    policy_json_str = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    plan_obj = [
        {
            "function": "create_aws_iam_role",
            "args": {
                "label": "lambda_exec",
                "name": "lambda-exec-role",
                "assume_role_policy": policy_json_str,
            },
            "assign": "iam_role_hcl",
        }
    ]
    raw = json.dumps(plan_obj)
    result = _extract_json_array(raw)
    assert result is not None, "Parser returned None on nested-brace input"
    parsed = json.loads(result)
    assert parsed[0]["args"]["assume_role_policy"] == policy_json_str


def test_markdown_wrapped_output():
    """LLM sometimes wraps JSON in ```json ... ``` fences."""
    inner = '[{"function": "log_message", "args": {"message": "hi"}}]'
    raw = f"```json\n{inner}\n```"
    result = _extract_json_array(raw)
    assert result is not None
    parsed = json.loads(result)
    assert parsed[0]["function"] == "log_message"


def test_leading_text_before_array():
    """Prose before the JSON array should be ignored."""
    inner = '[{"function": "log_message", "args": {"message": "test"}}]'
    raw = f"Sure! Here is your plan:\n{inner}"
    result = _extract_json_array(raw)
    assert result is not None
    parsed = json.loads(result)
    assert len(parsed) == 1


def test_empty_input():
    """Empty string returns None, not an exception."""
    assert _extract_json_array("") is None


def test_no_array_in_input():
    """Plain text with no JSON array returns None."""
    assert _extract_json_array("Sorry, I cannot help with that.") is None


def test_escaped_quote_inside_string():
    """Escaped quote characters inside strings must not confuse the parser."""
    raw = '[{"function": "log_message", "args": {"message": "say \\"hello\\" world"}}]'
    result = _extract_json_array(raw)
    assert result is not None
    parsed = json.loads(result)
    assert 'hello' in parsed[0]["args"]["message"]


def test_multi_step_plan():
    """Multi-step plan with variable references parses fully."""
    plan = [
        {"function": "create_aws_vpc", "args": {"label": "main", "cidr_block": "10.0.0.0/16"}, "assign": "vpc_hcl"},
        {"function": "create_aws_subnet", "args": {"label": "pub", "cidr_block": "10.0.1.0/24"}, "assign": "subnet_hcl"},
        {"function": "combine_hcl_blocks", "args": {"blocks": ["{vpc_hcl}", "{subnet_hcl}"]}, "assign": "combined"},
        {"function": "save_hcl_to_file", "args": {"hcl_content": "{combined}"}},
    ]
    raw = json.dumps(plan)
    result = _extract_json_array(raw)
    assert result is not None
    parsed = json.loads(result)
    assert len(parsed) == 4
    assert parsed[2]["function"] == "combine_hcl_blocks"


# ---------------------------------------------------------------------------
# combine_hcl_blocks list-param tests
# ---------------------------------------------------------------------------

def test_combine_hcl_blocks_list():
    """combine_hcl_blocks accepts a list and joins with double newline."""
    from agx.registries.utilities import combine_hcl_blocks
    result = combine_hcl_blocks(["a", "b", "c"])
    assert result == "a\n\nb\n\nc"


def test_combine_hcl_blocks_filters_empty():
    """Empty strings and whitespace-only entries are skipped."""
    from agx.registries.utilities import combine_hcl_blocks
    result = combine_hcl_blocks(["a", "", "  ", "b"])
    assert result == "a\n\nb"


def test_combine_hcl_blocks_single_string_fallback():
    """A bare string (not a list) is wrapped automatically."""
    from agx.registries.utilities import combine_hcl_blocks
    result = combine_hcl_blocks("hello")
    assert result == "hello"


# ---------------------------------------------------------------------------
# generate_plan integration (mocked LLM)
# ---------------------------------------------------------------------------

def test_generate_plan_parses_nested_brace_output():
    """generate_plan correctly returns a plan even when the LLM output
    contains nested braces inside string values (the Lambda/IAM case)."""
    policy = '{"Version":"2012-10-17"}'
    mock_output = json.dumps([
        {"function": "log_message", "args": {"message": policy}}
    ])
    with patch("agx.planner.generate_raw_json", return_value=mock_output):
        plan = generate_plan(prompt="create lambda role")
    assert len(plan) == 1
    assert plan[0]["args"]["message"] == policy


def test_generate_plan_returns_empty_on_no_json():
    """generate_plan returns [] when the LLM outputs no JSON array."""
    with patch("agx.planner.generate_raw_json", return_value="I cannot help with that."):
        plan = generate_plan(prompt="what is the weather?")
    assert plan == []


def test_generate_plan_returns_empty_on_invalid_json():
    """generate_plan returns [] when extracted text is invalid JSON."""
    with patch("agx.planner.generate_raw_json", return_value="[{broken json"):
        plan = generate_plan(prompt="bad output")
    assert plan == []
