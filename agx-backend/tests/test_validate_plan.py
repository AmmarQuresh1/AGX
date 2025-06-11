# Create agx/test_validate_plan.py
from agx.validate_plan import validate_plan

def test_valid_plan():
    """Test a completely valid plan"""
    plan = [
        {"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "result"},
        {"function": "log_message", "args": {"message": "Answer: {result}"}}
    ]
    assert validate_plan(plan) == True

def test_missing_function():
    """Test non-existent function"""
    plan = [{"function": "nonexistent_func", "args": {"x": 1}}]
    assert validate_plan(plan) == False

def test_missing_required_param():
    """Test missing required parameter"""
    plan = [{"function": "add_numbers", "args": {"a": 5}}]  # Missing 'b'
    assert validate_plan(plan) == False

def test_variable_before_assignment():
    """Test using variable before it's assigned"""
    plan = [
        {"function": "log_message", "args": {"message": "{undefined_var}"}}
    ]
    assert validate_plan(plan) == False

def test_your_sample_plan():
    """Test your actual sample plan from #sample_plan.json"""
    plan = [
        {"function": "say_hello", "args": {"name": "Ammar Qureshi"}},
        {"function": "log_message", "args": {"message": "AGX ran successfully."}}
    ]
    # This should fail because 'say_hello' doesn't exist in registry
    assert validate_plan(plan) == False

def test_missing_type_hints():
    """Test that validation catches missing type hints"""
    # This test expects validation to FAIL due to missing type hints
    plan = [{"function": "some_function_without_type_hints", "args": {"param": "value"}}]
    assert validate_plan(plan) == False  # ← This should fail validation

# Run tests
if __name__ == "__main__":
    test_valid_plan()
    test_missing_function() 
    test_missing_required_param()
    test_variable_before_assignment()
    test_your_sample_plan()
    test_missing_type_hints()
    print("All tests passed!")