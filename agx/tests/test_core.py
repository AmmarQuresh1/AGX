"""
test_core.py

Tests for the core AGX retry mechanism with validation feedback.
"""
from unittest.mock import patch, MagicMock
from agx.core import agx_main
from agx.validate_plan import validate_plan


def test_retry_success_after_failure():
    """Test that retry mechanism succeeds after initial validation failure"""
    # Mock generate_plan to return invalid plan first, then valid plan
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]
    valid_plan = [
        {"function": "log_message", "args": {"message": "test"}}
    ]
    
    call_count = [0]
    
    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None):
        call_count[0] += 1
        if call_count[0] == 1:
            # First call - return invalid plan
            return invalid_plan
        else:
            # Retry call - return valid plan
            return valid_plan
    
    with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
        with patch('agx.core.compile_plan', return_value="# Generated code\n"):
            result = agx_main("test prompt")
            
            # Should succeed after retry
            assert "code" in result
            assert call_count[0] == 2  # Initial attempt + 1 retry


def test_retry_exhausted():
    """Test that retry mechanism stops after max_retries"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]
    
    with patch('agx.core.generate_plan', return_value=invalid_plan):
        result = agx_main("test prompt", max_retries=2)
        
        # Should fail after exhausting retries
        assert "error" in result
        assert result["error"] == "validation_failed"
        assert result.get("retries_exhausted") is True
        assert "errors" in result


def test_no_retry_on_success():
    """Test that no retry occurs when plan is valid on first attempt"""
    valid_plan = [
        {"function": "log_message", "args": {"message": "test"}}
    ]
    
    call_count = [0]
    
    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None):
        call_count[0] += 1
        return valid_plan
    
    with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
        with patch('agx.core.compile_plan', return_value="# Generated code\n"):
            result = agx_main("test prompt")
            
            # Should succeed without retry
            assert "code" in result
            assert call_count[0] == 1  # Only one call, no retry


def test_validation_errors_passed_to_replan():
    """Test that validation errors and previous plan are passed to replanning"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]
    valid_plan = [{"function": "log_message", "args": {"message": "test"}}]
    
    validation_errors_received = []
    previous_plan_received = None
    
    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None):
        nonlocal previous_plan_received
        if validation_errors is not None:
            validation_errors_received.extend(validation_errors)
        if previous_plan is not None:
            previous_plan_received = previous_plan
        # Return valid plan on retry
        return valid_plan if validation_errors else invalid_plan
    
    with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
        with patch('agx.core.compile_plan', return_value="# Generated code\n"):
            result = agx_main("test prompt", max_retries=1)
            
            # Should have received validation errors and previous plan
            assert len(validation_errors_received) > 0
            assert previous_plan_received == invalid_plan
            assert "code" in result  # Should succeed after retry


def test_custom_max_retries():
    """Test that custom max_retries parameter works"""
    invalid_plan = [{"function": "nonexistent_func", "args": {}}]
    
    generate_plan_calls = []
    
    def mock_generate_plan(prompt=None, previous_plan=None, validation_errors=None):
        generate_plan_calls.append((previous_plan, validation_errors))
        return invalid_plan
    
    with patch('agx.core.generate_plan', side_effect=mock_generate_plan):
        result = agx_main("test prompt", max_retries=5)
        
        # Should have attempted max_retries + 1 times (initial + retries)
        assert len(generate_plan_calls) == 6
        assert result["error"] == "validation_failed"
        assert result.get("retries_exhausted") is True


def test_no_prompt_error():
    """Test that missing prompt returns appropriate error"""
    result = agx_main(None)
    
    assert "error" in result
    assert result["error"] == "no_prompt"

