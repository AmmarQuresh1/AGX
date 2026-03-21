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
    is_valid, errors = validate_plan(EXAMPLE_PLAN)
    assert is_valid is True
    assert errors == []


def test_missing_function():
    bad = [{"function": "nonexistent_func", "args": {"x": 1}}]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_variable_before_assignment():
    bad = [{"function": "log_message", "args": {"message": "{undefined_var}"}}]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_e2e_creates_main_tf():

    # Validate IR
    is_valid, errors = validate_plan(EXAMPLE_PLAN)
    assert is_valid is True
    assert errors == []

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
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_multi_variable_valid():
    """Test that valid multi-variable strings pass"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket_name"},
        {"function": "create_aws_s3_bucket", "args": {"label": "test", "bucket_name": "{bucket_name}"}, "assign": "bucket_id"},
        {"function": "save_hcl_to_file", "args": {"hcl_content": "{bucket_name}\n{bucket_id}"}}
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


def test_variable_in_middle_of_string():
    """Test variable reference in middle of string"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket_name"},
        {"function": "log_message", "args": {"message": "Bucket: {bucket_name} is ready"}}
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


def test_empty_variable_reference():
    """Empty {} is not a valid identifier pattern so it is not treated as a
    variable reference — the string passes through as a literal value."""
    plan = [
        {"function": "log_message", "args": {"message": "{}"}}
    ]
    is_valid, errors = validate_plan(plan)
    assert is_valid is True  # {} contains no identifier, not a var ref


# Type Checking Tests
def test_type_mismatch_str_expected_int_given():
    """Test that type mismatches are caught (str expected, int given)"""
    bad = [
        {"function": "set_bucket_name", "args": {"name": 12345}}  # name should be str
    ]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_type_mismatch_bool_expected_str_given():
    """Test that type mismatches are caught (bool expected, str given)"""
    bad = [
        {"function": "aws_s3_bucket_public_access_block", "args": {"label": "test", "block_all_public": "true"}}  # should be bool
    ]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_valid_bool_type():
    """Test that valid bool values pass"""
    valid = [
        {"function": "aws_s3_bucket_public_access_block", "args": {"label": "test", "block_all_public": True}}
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


def test_valid_str_type():
    """Test that valid str values pass"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "test-bucket"}}
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


# Parameter Validation Tests
def test_unknown_parameter():
    """Test that unknown parameters are caught"""
    bad = [
        {"function": "set_bucket_name", "args": {"name": "test", "unknown_param": "value"}}
    ]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_missing_required_parameter():
    """Test that missing required parameters are caught"""
    bad = [
        {"function": "create_aws_s3_bucket", "args": {"label": "test"}}  # missing bucket_name
    ]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_optional_parameter_default():
    """Test that optional parameters work with defaults"""
    valid = [
        {"function": "save_hcl_to_file", "args": {"hcl_content": "test"}}  # filename has default
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


def test_optional_parameter_provided():
    """Test that optional parameters can be provided"""
    valid = [
        {"function": "save_hcl_to_file", "args": {"hcl_content": "test", "filename": "custom.tf"}}
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


# Edge Cases
def test_empty_plan():
    """Test empty plan is rejected"""
    is_valid, errors = validate_plan([])
    assert is_valid is False
    assert len(errors) == 1
    assert "Empty plan" in errors[0]


def test_none_function():
    """Test plan with None function (should fail)"""
    bad = [{"function": None, "args": {}}]
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_missing_function_key():
    """Test plan missing function key"""
    bad = [{"args": {"name": "test"}}]
    # This will fail because fn = step.get("function") returns None
    is_valid, errors = validate_plan(bad)
    assert is_valid is False
    assert len(errors) > 0


def test_complex_variable_chain():
    """Test A→B→C variable dependency chain"""
    valid = [
        {"function": "set_bucket_name", "args": {"name": "a"}, "assign": "a"},
        {"function": "set_bucket_name", "args": {"name": "{a}"}, "assign": "b"},
        {"function": "set_bucket_name", "args": {"name": "{b}"}, "assign": "c"}
    ]
    is_valid, errors = validate_plan(valid)
    assert is_valid is True
    assert errors == []


def test_json_string_in_arg_not_treated_as_var_ref():
    """Regression: IAM assume_role_policy contains embedded JSON with {}.
    The validator must NOT flag inner JSON keys like {"Service":"..."} as
    undefined variable references."""
    policy = ('{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
              '"Principal":{"Service":"ec2.amazonaws.com"},'
              '"Action":"sts:AssumeRole"}]}')
    plan = [
        {"function": "log_message", "args": {"message": policy}}
    ]
    is_valid, errors = validate_plan(plan)
    assert is_valid is True, f"Unexpected errors: {errors}"


def test_json_string_does_not_shadow_real_var_errors():
    """Embedded JSON must not suppress genuine undefined-variable errors
    that happen to sit in the same argument value."""
    plan = [
        {"function": "log_message", "args": {"message": "{\"key\":\"val\"} see {undefined_var}"}}
    ]
    is_valid, errors = validate_plan(plan)
    assert is_valid is False
    assert any("undefined_var" in e for e in errors)