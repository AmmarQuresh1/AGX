"""
function_builder.py

Generates Python functions dynamically from Terraform resource schemas.
Each generated function takes a label + resource attributes and returns HCL.

The compiler needs both callable objects and source strings (since
inspect.getsource() doesn't work on exec()'d functions).
"""
from __future__ import annotations

from .registries.utilities import UTILITY_REGISTRY, UTILITY_SOURCE


# Maps our simplified type strings to Python type hints and defaults
_TYPE_MAP = {
    "string": ("str", '""'),
    "number": ("int", "0"),
    "bool": ("bool", "False"),
    "list(string)": ("str", '""'),    # Serialised as HCL list literal
    "map(string)": ("str", '""'),     # Serialised as HCL map literal
}


def _python_type(schema_type: str) -> str:
    return _TYPE_MAP.get(schema_type, ("str", '""'))[0]


def _python_default(schema_type: str) -> str:
    return _TYPE_MAP.get(schema_type, ("str", '""'))[1]


def _hcl_value_expr(attr_name: str, schema_type: str) -> str:
    """Return the f-string expression to render an attribute value in HCL."""
    if schema_type == "bool":
        # Terraform expects lowercase true/false
        return f'{{str({attr_name}).lower()}}'
    if schema_type == "number":
        return f'{{{attr_name}}}'
    if schema_type in ("list(string)", "map(string)"):
        # Passed as raw HCL literal strings — no quotes
        return f'{{{attr_name}}}'
    # Default: quoted string
    return f'{{{attr_name}}}'


def generate_hcl_function_source(resource_type: str, schema: dict) -> str:
    """
    Generate Python source for a function that returns Terraform HCL
    for the given resource type.

    Args:
        resource_type: e.g. "aws_s3_bucket"
        schema: {"required_attrs": {...}, "optional_attrs": {...}, "description": "..."}

    Returns:
        Python source code string defining the function.
    """
    func_name = f"create_{resource_type}"
    required = schema.get("required_attrs", {})
    optional = schema.get("optional_attrs", {})
    description = schema.get("description", f"Creates {resource_type} HCL")

    # Build parameter list: label first, then required, then optional with defaults
    params = ["label: str"]
    for attr, typ in required.items():
        params.append(f"{attr}: {_python_type(typ)}")
    for attr, typ in optional.items():
        params.append(f"{attr}: {_python_type(typ)} = {_python_default(typ)}")

    params_str = ", ".join(params)

    # Build HCL body lines
    body_lines = []
    body_lines.append(f"    lines = []")
    body_lines.append(f'    lines.append(\'resource "{resource_type}" "\'  + label + \'" {{\')')

    # Required attributes always rendered
    for attr, typ in required.items():
        if typ in ("number", "bool"):
            body_lines.append(f'    lines.append(f\'  {attr} = {_hcl_value_expr(attr, typ)}\')')
        elif typ in ("list(string)", "map(string)"):
            body_lines.append(f'    lines.append(f\'  {attr} = {_hcl_value_expr(attr, typ)}\')')
        else:
            body_lines.append(f'    lines.append(f\'  {attr} = "{_hcl_value_expr(attr, typ)}"\')')

    # Optional attributes rendered only if non-empty
    for attr, typ in optional.items():
        body_lines.append(f"    if {attr}:")
        if typ in ("number", "bool"):
            body_lines.append(f'        lines.append(f\'  {attr} = {_hcl_value_expr(attr, typ)}\')')
        elif typ in ("list(string)", "map(string)"):
            body_lines.append(f'        lines.append(f\'  {attr} = {_hcl_value_expr(attr, typ)}\')')
        else:
            body_lines.append(f'        lines.append(f\'  {attr} = "{_hcl_value_expr(attr, typ)}"\')')

    body_lines.append("    lines.append('}')")
    body_lines.append("    return '\\n'.join(lines)")

    source = f'def {func_name}({params_str}) -> str:\n'
    source += f'    """{description}"""\n'
    source += "\n".join(body_lines)

    return source


def build_dynamic_registry(resources: dict) -> tuple[dict, dict]:
    """
    Build a dynamic function registry from selected resource schemas.

    Args:
        resources: {resource_type: schema_dict, ...} from distillation

    Returns:
        (registry, source_map) where:
        - registry: {func_name: callable, ...} including utility functions
        - source_map: {func_name: source_code_string, ...} for compilation
    """
    registry = dict(UTILITY_REGISTRY)
    source_map = dict(UTILITY_SOURCE)

    for resource_type, schema in resources.items():
        func_name = f"create_{resource_type}"
        source = generate_hcl_function_source(resource_type, schema)

        # Compile and extract the callable
        namespace: dict = {}
        exec(compile(source, f"<agx:{func_name}>", "exec"), namespace)

        registry[func_name] = namespace[func_name]
        source_map[func_name] = source

    return registry, source_map


def build_prompt_fragment(registry: dict, source_map: dict) -> str:
    """
    Generate the 'Available functions' section for the planner prompt,
    listing every function in the registry with its signature and docstring.
    """
    import inspect

    lines = []
    for func_name, func in sorted(registry.items()):
        sig = inspect.signature(func)
        ret = sig.return_annotation
        ret_str = ret.__name__ if hasattr(ret, "__name__") else str(ret)
        doc = (func.__doc__ or "").strip().split("\n")[0]
        lines.append(f"- {func_name}{sig} -> {ret_str}  // {doc}")

    return "\n".join(lines)
