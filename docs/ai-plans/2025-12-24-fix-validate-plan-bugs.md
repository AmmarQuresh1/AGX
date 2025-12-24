# Fix validate_plan.py Bugs

## Goal
Assess and potentially fix two bugs in `validate_plan.py`:
1. **Variable reference validation bug**: Multi-variable strings (e.g., `"{var1}\n{var2}"`) are not checked for undefined variables
2. **Type checking leniency**: Type checking is bypassed due to `from __future__ import annotations` making type hints strings instead of type objects

**Note**: These may be theoretical bugs that don't manifest in practice given current system constraints.

## Affected Files
- `agx/validate_plan.py` - Main validation logic needs fixes
- `agx/tests/test_validate_plan.py` - Add test cases to verify fixes

## Research Findings

### Issue 1: Variable Reference Validation Bug
**Location**: Line 97 in `validate_plan.py`

**Problem**: 
- Current condition: `if isinstance(v, str) and re.match(r"^{.*}$", v)`
- This only matches strings that are EXACTLY `{variable_name}` (nothing else)
- Strings like `"{bucket_id}\n{pab_id}"` don't match, so validation is skipped
- The `re.findall()` on line 98 would correctly find all variables, but it's never reached

**Evidence**:
- Test case: `{"hcl_content": "{bucket_id}\n{undefined_var}"}` passes validation when it should fail
- Compiler correctly handles multi-variable strings (line 35 in `compiler.py` uses `"{" in v and "}" in v`)

**Practical Impact Assessment**:
- **Prompt template discourages newlines**: Line 29 says "with no additions(no newline characters etc)"
- **Dedicated function exists**: `combine_two_hcl_blocks(block1: str, block2: str)` is available for joining HCL blocks
- **LLM behavior**: The model would likely use `combine_two_hcl_blocks` instead of manual newline joins
- **Conclusion**: This bug may not manifest in practice, as the LLM is discouraged from generating this pattern

### Issue 2: Type Checking Leniency
**Location**: Lines 37-47 in `validate_plan.py`, specifically line 42

**Problem**:
- Registry uses `from __future__ import annotations` (line 7 in `devops_test.py`)
- This makes type hints strings (`"str"`) instead of type objects (`str`)
- Line 42 checks `isinstance(type_hint, type)` which is `False` for strings
- Function falls through to exception handler/fallback that always returns `True`
- Result: Type mismatches (e.g., `int` where `str` expected) are not caught

**Evidence**:
- Test: `{"name": 12345}` where `name: str` expected passes validation
- `_check_type(123, "str")` returns `True` when it should return `False`

**Practical Impact Assessment**:
- **Registry is mostly string-based**: All parameters except one are `str` (only `block_all_public: bool` is non-string)
- **JSON handles types correctly**: LLM generates JSON which naturally preserves types (`true` → Python `True`, `"string"` → Python `str`)
- **LLM behavior**: The model would generate proper JSON types that match function signatures
- **Conclusion**: Type mismatches are unlikely in practice, as JSON type system aligns with function signatures

## Test Coverage Analysis

### Current Test Coverage in `test_validate_plan.py`

**Existing Tests:**
- ✅ `test_valid_example_plan` - Valid multi-step plan with variables
- ✅ `test_missing_function` - Function existence check
- ✅ `test_variable_before_assignment` - Single variable reference before assignment
- ✅ `test_e2e_creates_main_tf` - End-to-end validation + compilation

**Missing Test Coverage:**

#### Validation Checks (from `validate_plan.py`):
1. ❌ **Unknown parameter** - Test invalid parameter names
2. ❌ **Missing type hints** - Test functions without type hints (if any exist)
3. ❌ **Type mismatches** - Test wrong types (str vs int, bool vs str, etc.)
4. ❌ **Missing required parameters** - Test plans missing required args
5. ❌ **Missing return type hints** - Test functions without return annotations (if any exist)
6. ❌ **Multi-variable strings** - Test multiple variables in one string (the bug)
7. ❌ **Multi-variable with undefined** - Test multi-var string with one undefined var
8. ❌ **Variable in non-string context** - Edge case (shouldn't happen but good to test)
9. ❌ **Empty string with variables** - Edge case
10. ❌ **Nested/escaped braces** - Edge case (e.g., `"{{var}}"` or `"{var1}{var2}"`)
11. ❌ **Valid bool type** - Test that `True`/`False` pass for `bool` parameters
12. ❌ **Invalid bool type** - Test that non-bool fails for `bool` parameters
13. ❌ **Optional parameters** - Test that optional params work correctly
14. ❌ **Empty plan** - Test empty plan validation
15. ❌ **None/null values** - Test None handling

### Current Test Coverage in `test_compiler.py`

**Existing Tests:**
- ✅ `test_simple_function_call` - Basic compilation
- ✅ `test_function_with_assignment` - Variable assignment
- ✅ `test_variable_reference` - Single variable in string
- ✅ `test_function_deduplication` - Duplicate function handling
- ✅ `test_multiple_data_types` - Different argument types
- ✅ `test_empty_plan` - Empty plan compilation
- ✅ `test_generated_code_is_executable` - Code execution
- ✅ `test_complex_plan` - Multi-variable strings

**Missing Test Coverage:**

1. ❌ **Multi-variable with newlines** - Test `"{var1}\n{var2}"` compilation
2. ❌ **Variable in middle of string** - Test `"prefix{var}suffix"` compilation
3. ❌ **Empty variable reference** - Edge case `"{}"` or `"{ }"`
4. ❌ **Nested braces** - Test `"{{var}}"` handling
5. ❌ **Special characters in strings** - Test quotes, escapes, etc.
6. ❌ **None values** - Test None handling in compilation
7. ❌ **Complex variable chains** - Test A→B→C variable dependencies
8. ❌ **Boolean values** - Test True/False compilation (already partially covered)

### Comprehensive Test Plan

#### Phase 1: Test Planning (Before Implementation)
Create comprehensive test cases covering all validation checks and edge cases.

#### Phase 2: Implementation
Fix the two bugs in `validate_plan.py`.

#### Phase 3: Test Suite Update
Add all missing test cases to verify fixes and ensure comprehensive coverage.

## Step-by-Step Implementation

### Step 1: Plan and Document Missing Test Cases
**Files**: `agx/tests/test_validate_plan.py`, `agx/tests/test_compiler.py`

**Action**: Document all missing test cases (see Test Coverage Analysis above) before implementing fixes.

### Step 2: Fix Variable Reference Validation
**File**: `agx/validate_plan.py`

**Change line 97**:
```python
# OLD:
if isinstance(v, str) and re.match(r"^{.*}$", v):

# NEW:
if isinstance(v, str) and "{" in v and "}" in v:
```

**Rationale**: 
- Matches compiler logic (line 35 in `compiler.py`)
- Checks if string contains any variable references, not just exact matches
- Allows `re.findall()` to properly extract all variable references

### Step 2: Fix Type Checking for Future Annotations
**File**: `agx/validate_plan.py`

**Update `_check_type` function** (lines 37-47):

```python
def _check_type(value, type_hint):
    # Accept Any and unknown typing forms without strict checks
    try:
        if str(type_hint) == 'typing.Any' or type_hint is typing.Any:
            return True
        
        # Handle string type hints from __future__ annotations
        if isinstance(type_hint, str):
            # Convert string hint to actual type
            type_map = {
                'str': str,
                'int': int,
                'bool': bool,
                'float': float,
                'None': type(None),
                'NoneType': type(None),
            }
            actual_type = type_map.get(type_hint)
            if actual_type is not None:
                return isinstance(value, actual_type)
            # For unknown string hints, be lenient (fallback)
            return True
        
        # Handle actual type objects
        if _is_basic_type(type_hint) and isinstance(type_hint, type):
            return isinstance(value, type_hint)
    except Exception:
        return True
    # Fallback: don't block on complex hints in the demo
    return True
```

**Rationale**:
- Detects string type hints from `__future__ annotations`
- Maps common string hints to actual types
- Maintains backward compatibility with actual type objects
- Keeps lenient fallback for unknown/complex types

### Step 3: Implement Fixes
**File**: `agx/validate_plan.py`

Apply both fixes from Steps 1 and 2.

### Step 4: Add Comprehensive Test Cases
**Files**: `agx/tests/test_validate_plan.py`, `agx/tests/test_compiler.py`

**Add test functions to `test_validate_plan.py`:**

```python
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
```

**Add test functions to `test_compiler.py`:**

```python
def test_multi_variable_with_newlines():
    """Test compilation of multi-variable strings with newlines"""
    plan = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket_name"},
        {"function": "create_aws_s3_bucket", "args": {"label": "test", "bucket_name": "{bucket_name}"}, "assign": "bucket_id"},
        {"function": "save_hcl_to_file", "args": {"hcl_content": "{bucket_id}\n{bucket_name}"}}
    ]
    code = compile_plan(plan)
    assert 'hcl_content=f"{bucket_id}\n{bucket_name}"' in code

def test_variable_in_middle_of_string():
    """Test variable reference in middle of string compilation"""
    plan = [
        {"function": "set_bucket_name", "args": {"name": "test"}, "assign": "bucket"},
        {"function": "log_message", "args": {"message": "Bucket: {bucket} is ready"}}
    ]
    code = compile_plan(plan)
    assert 'message=f"Bucket: {bucket} is ready"' in code

def test_complex_variable_chain_compilation():
    """Test A→B→C variable dependency chain compilation"""
    plan = [
        {"function": "set_bucket_name", "args": {"name": "a"}, "assign": "a"},
        {"function": "set_bucket_name", "args": {"name": "{a}"}, "assign": "b"},
        {"function": "log_message", "args": {"message": "Chain: {a} -> {b}"}}
    ]
    code = compile_plan(plan)
    assert "a = set_bucket_name(name='a')" in code
    assert "b = set_bucket_name(name=f\"{a}\")" in code
    assert 'message=f"Chain: {a} -> {b}"' in code
```

## Implementation Order

1. **Phase 1: Test Planning** ✅ (This document)
   - Analyze existing test coverage
   - Document missing test cases
   - Plan comprehensive test suite

2. **Phase 2: Implement Fixes**
   - Fix variable reference validation bug (Step 1)
   - Fix type checking for future annotations (Step 2)

3. **Phase 3: Update Test Suite**
   - Add all missing test cases (Step 4)
   - Verify fixes work correctly
   - Ensure no regressions

## Verification Plan

1. **Run existing tests** to establish baseline:
   ```bash
   pytest agx/tests/test_validate_plan.py -v
   pytest agx/tests/test_compiler.py -v
   ```

2. **Implement fixes** (Steps 1-2)

3. **Run tests again** - some should now pass that previously failed:
   - `test_multi_variable_undefined` should now catch the bug
   - `test_type_mismatch` should now catch type errors

4. **Add comprehensive test suite** (Step 4)

5. **Run full test suite**:
   ```bash
   pytest agx/tests/ -v
   ```
   - All new tests should pass
   - All existing tests should still pass (no regressions)

6. **Integration test**:
   - Run full test suite to ensure no breaking changes
   - Verify `agx.core.agx_main` still works correctly
   - Test with real example plans

## Risk Assessment

**Low Risk**:
- Changes are isolated to validation logic
- No changes to external APIs or function signatures
- Backward compatible (existing valid plans will still pass)

**Mitigation**:
- Comprehensive test coverage before and after
- Preserve existing behavior for valid cases
- Maintain lenient fallback for complex/unknown types

## Decision: Proceed with Fixes

**Decision**: Fix both bugs and add comprehensive test coverage.

**Rationale**:
- Defensive programming - catch edge cases even if unlikely
- Consistency with compiler behavior (compiler handles multi-var strings)
- Future-proofing if registry expands to more types
- Comprehensive test coverage will improve code quality and maintainability
- Better validation catches errors earlier in the development cycle

## Notes

- The type checking fix handles the most common types (str, int, bool, float, None)
- For less common types or complex typing constructs, the lenient fallback remains
- This matches the MVP scope - strict type checking can be enhanced post-MVP
- Variable reference fix aligns with compiler behavior for consistency
- Both fixes are implemented in the plan below, but may not be necessary for current system

---

## Implementation Summary

### Status: ✅ COMPLETE

**Implementation Date**: 2025-12-24

### What Was Fixed

1. **Variable Reference Validation Bug** (Line 97 in `validate_plan.py`)
   - **Before**: Only validated strings that were exactly `{variable}` (nothing else)
   - **After**: Now validates any string containing `{variable}` patterns
   - **Impact**: Multi-variable strings like `"{var1}\n{var2}"` now properly check all variables

2. **Type Checking for `__future__ annotations`** (Lines 37-47 in `validate_plan.py`)
   - **Before**: Type hints stored as strings (`"str"`) were not recognized, causing all type checks to pass
   - **After**: Added string-to-type mapping for common types (str, int, bool, float, None)
   - **Impact**: Type mismatches (e.g., `int` where `str` expected) are now caught

### Test Coverage

**Before**: 4 tests in `test_validate_plan.py`, 8 tests in `test_compiler.py` (12 total)

**After**: 20 tests in `test_validate_plan.py`, 11 tests in `test_compiler.py` (31 total)

**New Test Categories Added**:
- Multi-variable string validation (undefined vars, valid cases)
- Type checking (mismatches, valid types for str/bool)
- Parameter validation (unknown params, missing required, optional params)
- Edge cases (empty plans, None values, complex variable chains)
- Compiler edge cases (newlines, middle-of-string variables, complex chains)

### Test Results

```
✅ All 31 tests passing
✅ Manual verification confirmed fixes work correctly
✅ No regressions - all existing tests still pass
✅ Backward compatible - existing valid plans continue to work
```

### Files Modified

1. `agx/validate_plan.py`
   - Fixed variable reference validation (line 97)
   - Enhanced `_check_type` function to handle string type hints (lines 37-65)

2. `agx/tests/test_validate_plan.py`
   - Added 16 new test cases covering all validation scenarios

3. `agx/tests/test_compiler.py`
   - Added 3 new test cases for compiler edge cases

### Verification

- ✅ All existing tests pass (no regressions)
- ✅ All new tests pass (fixes verified)
- ✅ Manual verification confirms bugs are fixed
- ✅ No linting errors
- ✅ Full test suite: 31/31 tests passing

### Key Improvements

1. **Better Error Detection**: Multi-variable strings and type mismatches are now caught
2. **Comprehensive Testing**: 19 new test cases ensure robust validation
3. **Future-Proof**: Type checking system ready for registry expansion
4. **Consistency**: Validation logic now matches compiler behavior

