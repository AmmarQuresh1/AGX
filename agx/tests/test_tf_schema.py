"""Tests for the Terraform schema tree and build utilities."""
import json
from pathlib import Path

TREE_PATH = Path(__file__).parent.parent / "tf_schema" / "aws_resource_tree.json"

def _load_tree():
    return json.loads(TREE_PATH.read_text())


def test_tree_structure():
    tree = _load_tree()
    assert tree["provider"] == "aws"
    assert "service_groups" in tree
    assert len(tree["service_groups"]) > 0


def test_all_groups_have_descriptions():
    tree = _load_tree()
    for name, group in tree["service_groups"].items():
        assert "description" in group, f"Group '{name}' missing description"
        assert len(group["description"]) > 0, f"Group '{name}' has empty description"


def test_all_resources_have_descriptions():
    tree = _load_tree()
    for gname, group in tree["service_groups"].items():
        for rtype, rinfo in group["resources"].items():
            assert "description" in rinfo, f"{rtype} missing description"
            assert len(rinfo["description"]) > 0, f"{rtype} has empty description"


def test_attrs_are_typed():
    tree = _load_tree()
    valid_types = {"string", "number", "bool", "list(string)", "map(string)"}
    for gname, group in tree["service_groups"].items():
        for rtype, rinfo in group["resources"].items():
            for attr, typ in rinfo.get("required_attrs", {}).items():
                assert typ in valid_types, f"{rtype}.{attr} has invalid type '{typ}'"
            for attr, typ in rinfo.get("optional_attrs", {}).items():
                assert typ in valid_types, f"{rtype}.{attr} has invalid type '{typ}'"


def test_all_resource_types_start_with_aws():
    tree = _load_tree()
    for gname, group in tree["service_groups"].items():
        for rtype in group["resources"]:
            assert rtype.startswith("aws_"), f"Resource '{rtype}' doesn't start with aws_"


def test_expected_groups_present():
    tree = _load_tree()
    expected = {"s3", "ec2", "iam", "vpc", "lambda", "dynamodb", "rds", "sns", "sqs", "cloudwatch"}
    actual = set(tree["service_groups"].keys())
    assert expected.issubset(actual), f"Missing groups: {expected - actual}"


def test_s3_bucket_in_tree():
    tree = _load_tree()
    s3 = tree["service_groups"]["s3"]["resources"]
    assert "aws_s3_bucket" in s3
    assert "bucket" in s3["aws_s3_bucket"]["required_attrs"]
