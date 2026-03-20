"""Tests for DAG construction and validation."""
import pytest
from agx.dag import (
    build_dag,
    topological_sort,
    validate_plan_ordering,
    validate_completeness,
    load_dependency_map,
)


SIMPLE_DEP_MAP = {
    "aws_s3_bucket_policy": ["aws_s3_bucket"],
    "aws_s3_bucket_public_access_block": ["aws_s3_bucket"],
    "aws_subnet": ["aws_vpc"],
    "aws_security_group": ["aws_vpc"],
    "aws_instance": ["aws_subnet", "aws_security_group"],
}


def test_topological_sort_simple():
    adj = {
        "aws_vpc": [],
        "aws_subnet": ["aws_vpc"],
        "aws_instance": ["aws_subnet"],
    }
    order = topological_sort(adj)
    assert order.index("aws_vpc") < order.index("aws_subnet")
    assert order.index("aws_subnet") < order.index("aws_instance")


def test_topological_sort_diamond():
    adj = {
        "aws_vpc": [],
        "aws_subnet": ["aws_vpc"],
        "aws_security_group": ["aws_vpc"],
        "aws_instance": ["aws_subnet", "aws_security_group"],
    }
    order = topological_sort(adj)
    assert order.index("aws_vpc") < order.index("aws_subnet")
    assert order.index("aws_vpc") < order.index("aws_security_group")
    assert order.index("aws_subnet") < order.index("aws_instance")
    assert order.index("aws_security_group") < order.index("aws_instance")


def test_cycle_detection():
    adj = {
        "a": ["b"],
        "b": ["a"],
    }
    with pytest.raises(ValueError, match="cycle"):
        topological_sort(adj)


def test_build_dag():
    selected = ["aws_s3_bucket", "aws_s3_bucket_policy"]
    dag = build_dag(selected, SIMPLE_DEP_MAP)
    assert "aws_s3_bucket" in dag["adjacency"]
    assert "aws_s3_bucket_policy" in dag["adjacency"]
    assert dag["adjacency"]["aws_s3_bucket_policy"] == ["aws_s3_bucket"]
    assert dag["missing_deps"] == []


def test_build_dag_missing_deps():
    selected = ["aws_s3_bucket_policy"]  # Missing aws_s3_bucket
    dag = build_dag(selected, SIMPLE_DEP_MAP)
    assert "aws_s3_bucket" in dag["missing_deps"]


def test_validate_ordering_correct():
    plan = [
        {"function": "create_aws_vpc", "args": {}},
        {"function": "create_aws_subnet", "args": {}},
        {"function": "create_aws_instance", "args": {}},
    ]
    topo_order = ["aws_vpc", "aws_subnet", "aws_instance"]
    errors = validate_plan_ordering(plan, topo_order)
    assert errors == []


def test_validate_ordering_wrong():
    plan = [
        {"function": "create_aws_instance", "args": {}},
        {"function": "create_aws_vpc", "args": {}},
        {"function": "create_aws_subnet", "args": {}},
    ]
    topo_order = ["aws_vpc", "aws_subnet", "aws_instance"]
    errors = validate_plan_ordering(plan, topo_order)
    assert len(errors) > 0
    assert "aws_instance" in errors[0]


def test_validate_completeness_all_present():
    plan = [
        {"function": "create_aws_s3_bucket", "args": {}},
        {"function": "create_aws_s3_bucket_policy", "args": {}},
    ]
    errors = validate_completeness(plan, SIMPLE_DEP_MAP)
    assert errors == []


def test_validate_completeness_missing_dep():
    plan = [
        {"function": "create_aws_s3_bucket_policy", "args": {}},
    ]
    errors = validate_completeness(plan, SIMPLE_DEP_MAP)
    assert len(errors) > 0
    assert "aws_s3_bucket" in errors[0]


def test_unknown_resources_ignored():
    """Resources not in the dep map should pass through without false positives."""
    plan = [
        {"function": "create_aws_cloudwatch_log_group", "args": {}},
    ]
    errors = validate_completeness(plan, SIMPLE_DEP_MAP)
    assert errors == []


def test_utility_functions_not_checked():
    """Non-create_ functions should be ignored by ordering validation."""
    plan = [
        {"function": "log_message", "args": {"message": "starting"}},
        {"function": "create_aws_vpc", "args": {}},
        {"function": "create_aws_subnet", "args": {}},
    ]
    topo_order = ["aws_vpc", "aws_subnet"]
    errors = validate_plan_ordering(plan, topo_order)
    assert errors == []


def test_load_dependency_map():
    dep_map = load_dependency_map()
    assert isinstance(dep_map, dict)
    assert "aws_s3_bucket_policy" in dep_map
    assert "aws_s3_bucket" in dep_map["aws_s3_bucket_policy"]
