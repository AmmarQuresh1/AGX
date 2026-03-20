"""
core.py

Main backend orchestrator for AGX.
- Initializes the backend.
- Distils a dynamic registry from the user prompt.
- Builds DAG for resource ordering validation.
- Loads and validates the plan.
- Executes the plan if valid.
- Implements bounded retry with validation feedback.
- Prints final output messages.
"""
from pathlib import Path
from .compiler import compile_plan
from .planner import generate_plan
from .validate_plan import validate_plan
from .distill import distill_registry
from .function_builder import build_dynamic_registry, build_prompt_fragment
from .dag import load_dependency_map, build_dag, topological_sort, validate_plan_ordering, validate_completeness
from typing import Optional

# Maximum number of retry attempts when validation fails
MAX_RETRIES = 3


def agx_main(prompt: Optional[str] = None, max_retries: int = MAX_RETRIES):
    """
    Main AGX orchestrator. Returns a dict with either 'code' or 'error'.

    Flow:
    1. Distil registry (2-pass LLM) to select relevant AWS resources
    2. Build dynamic functions from resource schemas
    3. Build DAG for dependency validation
    4. Plan → Validate → Compile with retry loop
    """
    if not prompt:
        print("[AGX] No prompt provided")
        return {"error": "no_prompt"}

    # --- Step 1: Registry Distillation ---
    print("[AGX] Distilling registry for prompt...")
    try:
        from .llm_openai import call_llm
        distill_result = distill_registry(prompt, call_llm)
    except Exception as e:
        print(f"[AGX] Registry distillation failed: {e}")
        return {"error": f"distillation_failed: {e}"}

    if distill_result["error"]:
        print(f"[AGX] Distillation error: {distill_result['error']}")
        return {"error": distill_result["error"]}

    resources = distill_result["resources"]
    print(f"[AGX] Selected {len(resources)} resource types: {list(resources.keys())}")

    # --- Step 2: Build Dynamic Registry ---
    registry, source_map = build_dynamic_registry(resources)
    prompt_fragment = build_prompt_fragment(registry, source_map)
    print(f"[AGX] Built dynamic registry with {len(registry)} functions")

    # --- Step 3: Build DAG ---
    resource_types = list(resources.keys())
    dep_map = load_dependency_map()
    dag = build_dag(resource_types, dep_map)

    if dag["missing_deps"]:
        print(f"[AGX] Warning: missing dependency resources: {dag['missing_deps']}")

    try:
        topo_order = topological_sort(dag["adjacency"])
        print(f"[AGX] Topological order: {topo_order}")
    except ValueError as e:
        print(f"[AGX] DAG error: {e}")
        return {"error": f"dependency_cycle: {e}"}

    # --- Step 4: Plan → Validate → Compile ---
    retry_count = 0
    validation_errors = []
    previous_plan = None

    while retry_count <= max_retries:
        if retry_count > 0:
            print(f"[AGX] Retry attempt {retry_count}/{max_retries}...")

        plan = generate_plan(
            prompt=prompt,
            previous_plan=previous_plan if retry_count > 0 else None,
            validation_errors=validation_errors if retry_count > 0 else None,
            prompt_fragment=prompt_fragment,
        )

        # Structural validation (function existence, types, variable refs)
        is_valid, errors = validate_plan(plan, registry=registry)

        # DAG completeness — unfixable by planner, fail fast
        completeness_errors = validate_completeness(plan, dep_map)
        if completeness_errors:
            print(f"[AGX] Missing dependency resources (cannot retry): {completeness_errors}")
            return {"error": "missing_dependencies", "errors": completeness_errors}

        # DAG ordering — fixable by planner via retry
        ordering_errors = validate_plan_ordering(plan, topo_order)

        all_errors = errors + ordering_errors
        if not all_errors:
            print("[AGX] Compiling plan...")
            code = compile_plan(plan, registry=registry, source_map=source_map)

            if code:
                return {"code": code}
            else:
                print("[AGX] Compilation failed.")
                return {"error": "compilation_failed"}
        else:
            previous_plan = plan
            validation_errors = all_errors
            retry_count += 1

            if retry_count > max_retries:
                print(f"[AGX] Plan validation failed after {max_retries} retries - cannot compile.")
                return {"error": "validation_failed", "errors": all_errors, "retries_exhausted": True}

            print(f"[AGX] Plan validation failed ({len(all_errors)} errors). Retrying with feedback...")
