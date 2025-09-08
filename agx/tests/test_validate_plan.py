from agx.registries.devops_test import validate_plan, registry, EXAMPLE_PLAN, execute_plan
import os


def test_valid_example_plan():
    # Should raise no errors
    validate_plan(EXAMPLE_PLAN, registry)


def test_missing_function():
    bad = [{"function": "nonexistent_func", "args": {"x": 1}}]
    try:
        validate_plan(bad, registry)
    except ValueError as e:
        assert "is not allowed" in str(e)
    else:
        assert False, "Expected ValueError for missing function"


def test_variable_before_assignment():
    bad = [{"function": "log_message", "args": {"message": "{undefined_var}"}}]
    try:
        validate_plan(bad, registry)
    except ValueError as e:
        assert "references undefined variable" in str(e)
    else:
        assert False, "Expected ValueError for undefined variable reference"


def test_e2e_creates_main_tf(tmp_path):
    # Execute the example using a temp main.tf path
    plan = [dict(step) for step in EXAMPLE_PLAN]
    plan[-1] = {
        **plan[-1],
        "args": {**plan[-1]["args"], "filename": str(tmp_path / "main.tf")},
    }

    validate_plan(plan, registry)
    execute_plan(plan, registry)

    tf = tmp_path / "main.tf"
    assert tf.exists()
    content = tf.read_text(encoding="utf-8")
    assert "aws_s3_bucket" in content
    assert "aws_s3_bucket_public_access_block" in content