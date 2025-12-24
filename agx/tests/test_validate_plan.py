from pathlib import Path
from agx.validate_plan import validate_plan
from agx.compiler import compile_plan

EXAMPLE_PLAN = [
    {"function": "set_bucket_name", "args": {"name": "my-demo-bucket"}, "assign": "bucket_name"},
    {"function": "create_aws_s3_bucket", "args": {"label": "demo_bucket", "bucket_name": "{bucket_name}"}, "assign": "bucket_id"},
    {"function": "aws_s3_bucket_public_access_block", "args": {"label": "demo_bucket", "block_all_public": True}, "assign": "pab_id"},
    {"function": "save_hcl_to_file", "args": {"hcl_content": "{bucket_id}\\n{pab_id}", "filename": "main.tf"}}
]

def test_valid_example_plan():
    # Should raise no errors
    assert validate_plan(EXAMPLE_PLAN) is True


def test_missing_function():
    bad = [{"function": "nonexistent_func", "args": {"x": 1}}]
    assert validate_plan(bad) is False


def test_variable_before_assignment():
    bad = [{"function": "log_message", "args": {"message": "{undefined_var}"}}]
    assert validate_plan(bad) is False


def test_e2e_creates_main_tf():

    # Validate IR
    assert validate_plan(EXAMPLE_PLAN) is True

    # Compile to py code and run
    code = compile_plan(EXAMPLE_PLAN)
    print(code)
    exec(code, {'__name__': '__main__'})

    # Assert file and content
    tf = Path("main.tf")
    assert tf.exists()
    content = tf.read_text(encoding="utf-8")
    assert "aws_s3_bucket" in content
    assert "aws_s3_bucket_public_access_block" in content


# Variable Reference Tests
def test_multi_variable_undefined():
    """Test that undefined variables in multi-variable strings are caught"""
    bad = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket_name"},
        {"function": "save_hcl_to_file", "args": {"hcl_content": "{bucket_name}\n{undefined_var}"}}
    ]
    assert validate_plan(bad) is False


def test_multi_variable_valid():
    """Test that valid multi-variable strings pass"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket_name"},
        {"function": "create_aws_s3_bucket", "args": {"label": "test", "bucket_name": "{bucket_name}"}, "assign": "bucket_id"},
        {"function": "save_hcl_to_file", "args": {"hcl_content": "{bucket_name}\n{bucket_id}"}}
    ]
    assert validate_plan(valid) is True


def test_variable_in_middle_of_string():
    """Test variable reference in middle of string"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket_name"},
        {"function": "log_message", "args": {"message": "Bucket: {bucket_name} is ready"}}
    ]
    assert validate_plan(valid) is True


def test_empty_variable_reference():
    """Test edge case of empty variable reference"""
    bad = [
        {"function": "log_message", "args": {"message": "{}"}}
    ]
    assert validate_plan(bad) is False  # Empty var name should fail


# Type Checking Tests
def test_type_mismatch_str_expected_int_given():
    """Test that type mismatches are caught (str expected, int given)"""
    bad = [
        {"function": "set_bucket_name", "args": {"name": 12345}}  # name should be str
    ]
    assert validate_plan(bad) is False


def test_type_mismatch_bool_expected_str_given():
    """Test that type mismatches are caught (bool expected, str given)"""
    bad = [
        {"function": "aws_s3_bucket_public_access_block", "args": {"label": "test", "block_all_public": "true"}}  # should be bool
    ]
    assert validate_plan(bad) is False


def test_valid_bool_type():
    """Test that valid bool values pass"""
    valid = [
        {"function": "aws_s3_bucket_public_access_block", "args": {"label": "test", "block_all_public": True}}
    ]
    assert validate_plan(valid) is True


def test_valid_str_type():
    """Test that valid str values pass"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "test-bucket"}}
    ]
    assert validate_plan(valid) is True


# Parameter Validation Tests
def test_unknown_parameter():
    """Test that unknown parameters are caught"""
    bad = [
        {"function": "set_bucket_name", "args": {"name": "test", "unknown_param": "value"}}
    ]
    assert validate_plan(bad) is False


def test_missing_required_parameter():
    """Test that missing required parameters are caught"""
    bad = [
        {"function": "create_aws_s3_bucket", "args": {"label": "test"}}  # missing bucket_name
    ]
    assert validate_plan(bad) is False


def test_optional_parameter_default():
    """Test that optional parameters work with defaults"""
    valid = [
        {"function": "save_hcl_to_file", "args": {"hcl_content": "test"}}  # filename has default
    ]
    assert validate_plan(valid) is True


def test_optional_parameter_provided():
    """Test that optional parameters can be provided"""
    valid = [
        {"function": "save_hcl_to_file", "args": {"hcl_content": "test", "filename": "custom.tf"}}
    ]
    assert validate_plan(valid) is True


# Edge Cases
def test_empty_plan():
    """Test empty plan validation"""
    assert validate_plan([]) is True


def test_none_function():
    """Test plan with None function (should fail)"""
    bad = [{"function": None, "args": {}}]
    assert validate_plan(bad) is False


def test_missing_function_key():
    """Test plan missing function key"""
    bad = [{"args": {"name": "test"}}]
    # This will fail because fn = step.get("function") returns None
    assert validate_plan(bad) is False


def test_complex_variable_chain():
    """Test A→B→C variable dependency chain"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "a"}, "assign": "a"},
        {"function": "set_bucket_name", "args": {"name": "{a}"}, "assign": "b"},
        {"function": "set_bucket_name", "args": {"name": "{b}"}, "assign": "c"}
    ]
    assert validate_plan(valid) is True