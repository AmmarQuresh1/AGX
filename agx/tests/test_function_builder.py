"""Tests for dynamic function generation from Terraform schemas."""
import inspect
from agx.function_builder import generate_hcl_function_source, build_dynamic_registry, build_prompt_fragment


SAMPLE_SCHEMA = {
    "aws_s3_bucket": {
        "description": "Provides an S3 bucket resource",
        "required_attrs": {"bucket": "string"},
        "optional_attrs": {"force_destroy": "bool", "tags": "map(string)"},
    },
    "aws_vpc": {
        "description": "Provides a VPC resource",
        "required_attrs": {"cidr_block": "string"},
        "optional_attrs": {"enable_dns_support": "bool"},
    },
}


def test_generates_valid_python():
    source = generate_hcl_function_source("aws_s3_bucket", SAMPLE_SCHEMA["aws_s3_bucket"])
    # Should compile without SyntaxError
    compile(source, "<test>", "exec")


def test_generated_fn_returns_hcl():
    source = generate_hcl_function_source("aws_s3_bucket", SAMPLE_SCHEMA["aws_s3_bucket"])
    ns = {}
    exec(compile(source, "<test>", "exec"), ns)
    fn = ns["create_aws_s3_bucket"]
    hcl = fn(label="test", bucket="my-bucket")
    assert 'resource "aws_s3_bucket"' in hcl
    assert "my-bucket" in hcl


def test_required_attrs_are_required():
    source = generate_hcl_function_source("aws_s3_bucket", SAMPLE_SCHEMA["aws_s3_bucket"])
    ns = {}
    exec(compile(source, "<test>", "exec"), ns)
    fn = ns["create_aws_s3_bucket"]
    # Missing required 'bucket' param should raise TypeError
    try:
        fn(label="test")
        assert False, "Expected TypeError for missing required param"
    except TypeError:
        pass


def test_optional_attrs_have_defaults():
    source = generate_hcl_function_source("aws_s3_bucket", SAMPLE_SCHEMA["aws_s3_bucket"])
    ns = {}
    exec(compile(source, "<test>", "exec"), ns)
    fn = ns["create_aws_s3_bucket"]
    # Should work without optional params
    hcl = fn(label="test", bucket="my-bucket")
    assert "force_destroy" not in hcl  # Not rendered when default (False)


def test_optional_bool_rendered_when_set():
    source = generate_hcl_function_source("aws_s3_bucket", SAMPLE_SCHEMA["aws_s3_bucket"])
    ns = {}
    exec(compile(source, "<test>", "exec"), ns)
    fn = ns["create_aws_s3_bucket"]
    hcl = fn(label="test", bucket="my-bucket", force_destroy=True)
    assert "force_destroy" in hcl
    assert "true" in hcl


def test_label_always_first_param():
    source = generate_hcl_function_source("aws_vpc", SAMPLE_SCHEMA["aws_vpc"])
    ns = {}
    exec(compile(source, "<test>", "exec"), ns)
    fn = ns["create_aws_vpc"]
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    assert params[0] == "label"


def test_build_dynamic_registry():
    registry, source_map = build_dynamic_registry(SAMPLE_SCHEMA)
    # Should contain resource functions + utility functions
    assert "create_aws_s3_bucket" in registry
    assert "create_aws_vpc" in registry
    assert "log_message" in registry
    assert "save_hcl_to_file" in registry
    # Source map should have entries for all
    assert "create_aws_s3_bucket" in source_map
    assert "log_message" in source_map


def test_utility_functions_included():
    registry, source_map = build_dynamic_registry({})
    assert "log_message" in registry
    assert "save_hcl_to_file" in registry
    assert "sanitise_resource_name" in registry
    assert "combine_hcl_blocks" in registry


def test_build_prompt_fragment():
    registry, source_map = build_dynamic_registry(SAMPLE_SCHEMA)
    fragment = build_prompt_fragment(registry, source_map)
    assert "create_aws_s3_bucket" in fragment
    assert "create_aws_vpc" in fragment
    assert "log_message" in fragment
    assert "label" in fragment  # All functions have label param
