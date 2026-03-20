"""
dag.py

DAG construction and validation for Terraform resource ordering.

Builds a dependency graph from selected resources using a hand-curated
dependency map, then validates that LLM-generated plans respect the
topological ordering and include all required dependencies.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path


def load_dependency_map() -> dict[str, list[str]]:
    """Load the AWS dependency map from the JSON file."""
    path = Path(__file__).parent / "tf_schema" / "aws_dependency_map.json"
    return json.loads(path.read_text())


def build_dag(selected_resources: list[str], dep_map: dict[str, list[str]]) -> dict:
    """
    Build an adjacency list for the selected resources.

    Returns:
        {
            "adjacency": {node: [dependencies], ...},
            "missing_deps": [resource_types required but not in selection]
        }
    """
    adjacency: dict[str, list[str]] = {}
    missing_deps: list[str] = []

    selected_set = set(selected_resources)

    for resource in selected_resources:
        deps = dep_map.get(resource, [])
        # Only include deps that are in our selection
        present_deps = [d for d in deps if d in selected_set]
        absent_deps = [d for d in deps if d not in selected_set]
        adjacency[resource] = present_deps
        missing_deps.extend(absent_deps)

        # Ensure dependency nodes also appear in adjacency
        for dep in present_deps:
            if dep not in adjacency:
                adjacency[dep] = [d for d in dep_map.get(dep, []) if d in selected_set]

    return {
        "adjacency": adjacency,
        "missing_deps": sorted(set(missing_deps)),
    }


def topological_sort(adjacency: dict[str, list[str]]) -> list[str]:
    """
    Kahn's algorithm for topological sort.

    Args:
        adjacency: {node: [nodes this node depends on], ...}

    Returns:
        List of nodes in valid execution order (dependencies first).

    Raises:
        ValueError: If the graph contains a cycle.
    """
    # Build reverse graph (who depends on me) and in-degree counts
    reverse: dict[str, list[str]] = {n: [] for n in adjacency}
    in_degree: dict[str, int] = {n: 0 for n in adjacency}

    for node, deps in adjacency.items():
        for dep in deps:
            if dep in reverse:
                reverse[dep].append(node)
            in_degree[node] = in_degree.get(node, 0)

    # Count actual in-degrees from dependencies
    for node, deps in adjacency.items():
        count = sum(1 for d in deps if d in adjacency)
        in_degree[node] = count

    queue = deque(n for n, deg in in_degree.items() if deg == 0)
    result: list[str] = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for dependent in reverse.get(node, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(adjacency):
        visited = set(result)
        cycle_nodes = [n for n in adjacency if n not in visited]
        raise ValueError(f"Dependency cycle detected involving: {cycle_nodes}")

    return result


def validate_plan_ordering(plan: list[dict], topo_order: list[str]) -> list[str]:
    """
    Check that plan steps respect the topological ordering.

    Each step's function name is expected to be ``create_{resource_type}``.
    For steps that don't match this pattern (utility functions), ordering
    is not enforced.

    Returns:
        List of error strings (empty means valid).
    """
    errors: list[str] = []

    # Build position map for resources in the topological order
    topo_position = {res: i for i, res in enumerate(topo_order)}

    # Track at which plan step each resource type first appears
    resource_step: dict[str, int] = {}
    for step_idx, step in enumerate(plan):
        fn = step.get("function", "")
        if fn.startswith("create_"):
            resource_type = fn.removeprefix("create_")
            if resource_type not in resource_step:
                resource_step[resource_type] = step_idx

    # Check ordering: for each resource, all its topo-predecessors must
    # appear at earlier plan steps
    adjacency_from_order = {}
    dep_map = load_dependency_map()

    for resource_type, step_idx in resource_step.items():
        deps = dep_map.get(resource_type, [])
        for dep in deps:
            if dep in resource_step and resource_step[dep] > step_idx:
                errors.append(
                    f"[DAG Error] '{resource_type}' at step {step_idx + 1} depends on "
                    f"'{dep}' which appears later at step {resource_step[dep] + 1}"
                )

    return errors


def validate_completeness(plan: list[dict], dep_map: dict[str, list[str]]) -> list[str]:
    """
    Check that all dependency resources are present in the plan.

    For example, if the plan creates ``aws_s3_bucket_policy`` but not
    ``aws_s3_bucket``, this is flagged as an error.

    Returns:
        List of error strings (empty means valid).
    """
    errors: list[str] = []

    # Collect all resource types created in the plan
    created_resources: set[str] = set()
    for step in plan:
        fn = step.get("function", "")
        if fn.startswith("create_"):
            created_resources.add(fn.removeprefix("create_"))

    # Check each created resource's dependencies
    for resource_type in created_resources:
        deps = dep_map.get(resource_type, [])
        for dep in deps:
            if dep not in created_resources:
                errors.append(
                    f"[DAG Error] '{resource_type}' requires '{dep}' "
                    f"but it is not created in the plan"
                )

    return errors
