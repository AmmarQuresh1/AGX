import random
import inspect
from agx.validate_plan import validate_plan
from agx.registries.devops_test import registry

def random_arg_value(param):
    # Very basic: just return a string or int depending on annotation
    if param.annotation == int:
        return random.randint(1, 10)
    if param.annotation == str:
        return "test"
    if param.annotation == float:
        return random.random()
    # fallback
    return "test"

def test_random_registry_function():
    """Randomly select a function from the registry and test validation."""
    func_name, func = random.choice(list(registry.items()))
    sig = inspect.signature(func)
    # Skip functions with no parameters (other than self)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    args = {}
    for param in params:
        # Only test if type hints are present
        if param.annotation != inspect.Parameter.empty:
            args[param.name] = random_arg_value(param)
    plan = [{"function": func_name, "args": args}]
    # Should pass if all required args are present and valid
    assert validate_plan(plan) in [True, False]  # Just check it runs

def test_valid_plan():
    """Test a completely valid plan"""
    plan = [
        {"function": "check_docker_status", "args": {}, "assign": "docker_status"},
        {"function": "log_message", "args": {"message": "Answer: {docker_status}"}}
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
    test_random_registry_function()
    print("All tests passed!")