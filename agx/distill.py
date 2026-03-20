"""
distill.py

Registry distillation: two-pass LLM pruning to select relevant AWS resources
for a given user prompt.

Pass 1: Select relevant service groups (e.g. "s3", "iam")
Pass 2: Select specific resource types within those groups

The result feeds into function_builder.py to create a dynamic registry.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, Optional


MAX_RESOURCES = 20


def load_resource_tree() -> dict:
    """Load aws_resource_tree.json and return the parsed dict."""
    path = Path(__file__).parent / "tf_schema" / "aws_resource_tree.json"
    return json.loads(path.read_text())


def get_group_summaries(tree: dict) -> list[dict]:
    """
    Return a list of service group summaries for Pass 1.

    Each entry: {"name": "s3", "description": "Object storage..."}
    """
    groups = tree.get("service_groups", {})
    return [
        {"name": name, "description": info["description"]}
        for name, info in sorted(groups.items())
    ]


def get_resources_for_groups(tree: dict, group_names: list[str]) -> list[dict]:
    """
    Expand selected group names into a flat list of resource entries.

    Each entry: {"type": "aws_s3_bucket", "description": "...", "attrs": [...]}
    """
    groups = tree.get("service_groups", {})
    result = []
    for gname in group_names:
        group = groups.get(gname)
        if not group:
            continue
        for rtype, rinfo in group["resources"].items():
            attr_names = list(rinfo.get("required_attrs", {}).keys()) + list(rinfo.get("optional_attrs", {}).keys())
            result.append({
                "type": rtype,
                "description": rinfo["description"],
                "attrs": attr_names,
            })
    return result


def _extract_json_array(raw: str) -> list:
    """Extract the first JSON array from raw LLM output."""
    match = re.search(r"\[\s*.*?\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return []


def _build_pass1_prompt(task: str, summaries: list[dict]) -> str:
    """Build the group-selection prompt."""
    template_path = Path(__file__).parent / "prompt_templates" / "distill_pass1.txt"
    template = template_path.read_text()

    group_lines = "\n".join(
        f"- {s['name']}: {s['description']}" for s in summaries
    )
    prompt = template.replace("{{TASK}}", task)
    prompt = prompt.replace("{{GROUP_LIST}}", group_lines)
    return prompt


def _build_pass2_prompt(task: str, resources: list[dict]) -> str:
    """Build the resource-selection prompt."""
    template_path = Path(__file__).parent / "prompt_templates" / "distill_pass2.txt"
    template = template_path.read_text()

    resource_lines = "\n".join(
        f"- {r['type']}: {r['description']} (attrs: {', '.join(r['attrs'])})"
        for r in resources
    )
    prompt = template.replace("{{TASK}}", task)
    prompt = prompt.replace("{{RESOURCE_LIST}}", resource_lines)
    return prompt


def distill_registry(prompt: str, llm_call_fn: Callable[[str], str]) -> dict:
    """
    Two-pass LLM distillation to select relevant resources.

    Args:
        prompt: User's natural language infrastructure request
        llm_call_fn: Function that takes a prompt string and returns raw LLM output

    Returns:
        {
            "resources": {resource_type: schema_dict, ...} or None,
            "error": error_message or None
        }
    """
    tree = load_resource_tree()
    summaries = get_group_summaries(tree)

    if not summaries:
        return {"resources": None, "error": "No service groups available in resource tree"}

    # Pass 1: Select service groups
    pass1_prompt = _build_pass1_prompt(prompt, summaries)
    raw1 = llm_call_fn(pass1_prompt)
    selected_groups = _extract_json_array(raw1)

    # Ensure all items are strings
    selected_groups = [g for g in selected_groups if isinstance(g, str)]

    if not selected_groups:
        return {"resources": None, "error": "Non-infrastructure request — no relevant service groups identified"}

    # Pass 2: Select specific resources
    resources = get_resources_for_groups(tree, selected_groups)

    if not resources:
        return {"resources": None, "error": f"No resources found in selected groups: {selected_groups}"}

    pass2_prompt = _build_pass2_prompt(prompt, resources)
    raw2 = llm_call_fn(pass2_prompt)
    selected_types = _extract_json_array(raw2)

    # Ensure all items are strings
    selected_types = [t for t in selected_types if isinstance(t, str)]

    if not selected_types:
        return {"resources": None, "error": "No specific resources identified for this request"}

    if len(selected_types) > MAX_RESOURCES:
        return {
            "resources": None,
            "error": f"Request requires {len(selected_types)} resources (max {MAX_RESOURCES}). "
                     f"Please narrow the scope of your request."
        }

    # Build the resource schema dict from the tree
    groups = tree.get("service_groups", {})
    resource_schemas: dict = {}
    for gname in selected_groups:
        group = groups.get(gname, {})
        for rtype, rinfo in group.get("resources", {}).items():
            if rtype in selected_types:
                resource_schemas[rtype] = rinfo

    if not resource_schemas:
        return {"resources": None, "error": "Selected resource types not found in tree"}

    return {"resources": resource_schemas, "error": None}
