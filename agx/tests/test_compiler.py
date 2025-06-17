import random
from agx.compiler import compile_plan
from agx.registries.devops_test import registry

def test_simple_function_call():
    """Test basic function call generation"""
    plan = [{"function": "log_message", "args": {"message": "Hello"}}]
    code = compile_plan(plan)
    
    assert "def log_message(message: str) -> None:" in code
    assert "log_message(message='Hello')" in code
    assert 'if __name__ == "__main__":' in code

def test_function_with_assignment():
    """Test function call with variable assignment"""
    plan = [{"function": "build_docker_image", "args": {"image_name": "test_image", "dockerfile_path": "./app"}, "assign": "image_status"}]
    code = compile_plan(plan)
    
    assert "image_status = build_docker_image(image_name='test_image', dockerfile_path='./app')" in code

def test_variable_reference():
    """Test {variable} substitution in strings with registry functions"""
    plan = [
        {"function": "build_docker_image", "args": {"image_name": "test_image", "dockerfile_path": "./app"}, "assign": "build_status"},
        {"function": "log_message", "args": {"message": "Build result: {build_status}"}}
    ]
    code = compile_plan(plan)
    
    assert "build_status = build_docker_image(image_name='test_image', dockerfile_path='./app')" in code
    assert 'log_message(message=f"Build result: {build_status}")' in code

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
    plan = [{"function": "create_dockerfile", "args": {"app_type": "python", "port": 8080}}]
    code = compile_plan(plan)
    
    assert "create_dockerfile(app_type='python', port=8080)" in code

def test_empty_plan():
    """Test empty plan generates valid code"""
    plan = []
    code = compile_plan(plan)
    
    assert "def main():" in code
    assert 'if __name__ == "__main__":' in code

def test_generated_code_is_executable():
    """Test that generated code can be executed without errors"""
    plan = [{"function": "build_docker_image", "args": {"image_name": "test_image", "dockerfile_path": "./app"}, "assign": "result"}]
    code = compile_plan(plan)
    
    # This should not raise any exceptions
    compile(code, '<string>', 'exec')

def test_complex_plan():
    """Test a multi-step plan with variables"""
    plan = [
        {"function": "build_docker_image", "args": {"image_name": "img1", "dockerfile_path": "./app"}, "assign": "build1"},
        {"function": "build_docker_image", "args": {"image_name": "img2", "dockerfile_path": "./app2"}, "assign": "build2"}, 
        {"function": "log_message", "args": {"message": "First: {build1}, Second: {build2}"}}
    ]
    code = compile_plan(plan)
    
    assert "build1 = build_docker_image(image_name='img1', dockerfile_path='./app')" in code
    assert "build2 = build_docker_image(image_name='img2', dockerfile_path='./app2')" in code
    assert 'log_message(message=f"First: {build1}, Second: {build2}")' in code