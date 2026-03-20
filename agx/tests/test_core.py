"""
test_core.py

Tests for the core AGX retry mechanism with validation feedback.
The core pipeline now includes distillation + DAG steps, so these tests
mock those layers to isolate the retry logic.
"""
from unittest.mock import patch, MagicMock
from agx.core import agx_main
from agx.validate_plan import validate_plan


# A minimal distillation result that passes through to the plan/validate loop
_MOCK_DISTILL_OK = {
    "resources": {
        "aws_s3_bucket": {
            "description": "test",
            "required_attrs": {"bucket": "string"},
            "optional_attrs": {},
        }
    },
    "error": None,
}


def _patch_distill_and_dag():
    """Return a stack of patches that bypass distillation and DAG for unit tests."""
    return [
        patch("agx.core.distill_registry", return_value=_MOCK_DISTILL_OK),
        patch("agx.core.load_dependency_map", return_value={}),
        patch("agx.core.build_dag", return_value={"adjacency": {}, "missing_deps": []}),
        patch("agx.core.topological_sort", return_value=[]),
        patch("agx.core.validate_plan_ordering", return_value=[]),
        patch("agx.core.validate_completeness", return_value=[]),
    ]


def test_retry_success_after_failure():
    """Test that retry mechanism succeeds after initial validation failure"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]
    valid_plan = [
        {"function": "log_message", "args": {"message": "test"}}
    ]

    call_count = [0]

    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None, prompt_fragment=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return invalid_plan
        else:
            return valid_plan

    patches = _patch_distill_and_dag()
    for p in patches:
        p.start()
    try:
        with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
            with patch('agx.core.compile_plan', return_value="# Generated code\n"):
                result = agx_main("test prompt")

                assert "code" in result
                assert call_count[0] == 2
    finally:
        for p in patches:
            p.stop()


def test_retry_exhausted():
    """Test that retry mechanism stops after max_retries"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]

    patches = _patch_distill_and_dag()
    for p in patches:
        p.start()
    try:
        with patch('agx.core.generate_plan', return_value=invalid_plan):
            result = agx_main("test prompt", max_retries=2)

            assert "error" in result
            assert result["error"] == "validation_failed"
            assert result.get("retries_exhausted") is True
            assert "errors" in result
    finally:
        for p in patches:
            p.stop()


def test_no_retry_on_success():
    """Test that no retry occurs when plan is valid on first attempt"""
    valid_plan = [
        {"function": "log_message", "args": {"message": "test"}}
    ]

    call_count = [0]

    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None, prompt_fragment=None):
        call_count[0] += 1
        return valid_plan

    patches = _patch_distill_and_dag()
    for p in patches:
        p.start()
    try:
        with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
            with patch('agx.core.compile_plan', return_value="# Generated code\n"):
                result = agx_main("test prompt")

                assert "code" in result
                assert call_count[0] == 1
    finally:
        for p in patches:
            p.stop()


def test_validation_errors_passed_to_replan():
    """Test that validation errors and previous plan are passed to replanning"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]
    valid_plan = [{"function": "log_message", "args": {"message": "test"}}]

    validation_errors_received = []
    previous_plan_received = None

    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None, prompt_fragment=None):
        nonlocal previous_plan_received
        if validation_errors is not None:
            validation_errors_received.extend(validation_errors)
        if previous_plan is not None:
            previous_plan_received = previous_plan
        return valid_plan if validation_errors else invalid_plan

    patches = _patch_distill_and_dag()
    for p in patches:
        p.start()
    try:
        with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
            with patch('agx.core.compile_plan', return_value="# Generated code\n"):
                result = agx_main("test prompt", max_retries=1)

                assert len(validation_errors_received) > 0
                assert previous_plan_received == invalid_plan
                assert "code" in result
    finally:
        for p in patches:
            p.stop()


def test_custom_max_retries():
    """Test that custom max_retries parameter works"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]

    generate_plan_calls = []

    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None, prompt_fragment=None):
        generate_plan_calls.append((previous_plan, validation_errors))
        return invalid_plan

    patches = _patch_distill_and_dag()
    for p in patches:
        p.start()
    try:
        with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
            result = agx_main("test prompt", max_retries=5)

            assert len(generate_plan_calls) == 6
            assert result["error"] == "validation_failed"
            assert result.get("retries_exhausted") is True
    finally:
        for p in patches:
            p.stop()


def test_no_prompt_error():
    """Test that missing prompt returns appropriate error"""
    result = agx_main(None)

    assert "error" in result
    assert result["error"] == "no_prompt"


def test_distillation_error():
    """Test that distillation errors are returned properly"""
    with patch("agx.core.distill_registry", return_value={"resources": None, "error": "non-infrastructure request"}):
        result = agx_main("What is Terraform?")

    assert "error" in result
    assert "non-infrastructure" in result["error"]
