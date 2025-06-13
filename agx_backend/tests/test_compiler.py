from agx.compiler import compile_plan

def test_simple_function_call():
    """Test basic function call generation"""
    plan = [{"function": "log_message", "args": {"message": "Hello"}}]
    code = compile_plan(plan)
    
    assert "def log_message(message: str) -> None:" in code
    assert "log_message(message='Hello')" in code
    assert 'if __name__ == "__main__":' in code

def test_function_with_assignment():
    """Test function call with variable assignment"""
    plan = [{"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "result"}]
    code = compile_plan(plan)
    
    assert "result = add_numbers(a=2, b=3)" in code

def test_variable_reference():
    """Test {variable} substitution in strings"""
    plan = [
        {"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "sum"},
        {"function": "log_message", "args": {"message": "Result: {sum}"}}
    ]
    code = compile_plan(plan)
    
    assert 'log_message(message=f"Result: {sum}")' in code

def test_function_deduplication():
    """Test that duplicate functions aren't included twice"""
    plan = [
        {"function": "log_message", "args": {"message": "First"}},
        {"function": "log_message", "args": {"message": "Second"}}
    ]
    code = compile_plan(plan)
    
    # Should only have one function definition
    assert code.count("def log_message(") == 1
    # Should have both calls
    assert "log_message(message='First')" in code
    assert "log_message(message='Second')" in code

def test_multiple_data_types():
    """Test different argument types are handled correctly"""
    plan = [{"function": "add_numbers", "args": {"a": 2, "b": 3.5}}]
    code = compile_plan(plan)
    
    assert "add_numbers(a=2, b=3.5)" in code

def test_empty_plan():
    """Test empty plan generates valid code"""
    plan = []
    code = compile_plan(plan)
    
    assert "def main():" in code
    assert 'if __name__ == "__main__":' in code

def test_generated_code_is_executable():
    """Test that generated code can be executed without errors"""
    plan = [{"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "result"}]
    code = compile_plan(plan)
    
    # This should not raise any exceptions
    compile(code, '<string>', 'exec')

def test_complex_plan():
    """Test a multi-step plan with variables"""
    plan = [
        {"function": "add_numbers", "args": {"a": 5, "b": 10}, "assign": "sum1"},
        {"function": "add_numbers", "args": {"a": 2, "b": 3}, "assign": "sum2"}, 
        {"function": "log_message", "args": {"message": "First: {sum1}, Second: {sum2}"}}
    ]
    code = compile_plan(plan)
    
    assert "sum1 = add_numbers(a=5, b=10)" in code
    assert "sum2 = add_numbers(a=2, b=3)" in code
    assert 'log_message(message=f"First: {sum1}, Second: {sum2}")' in code