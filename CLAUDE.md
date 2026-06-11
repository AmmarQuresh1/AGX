# CLAUDE.md

## Project Overview

AGX is a single-shot agentic Terraform generator that constrains an LLM planner to a predefined function registry with static validation before compilation. It targets AWS infrastructure.

## Architecture

**Pipeline:** User Prompt → Registry Distillation (2-pass LLM) → Dynamic Function Generation → LLM Planning → Static Validation + DAG Check → Compilation → Executable Python Script

### Core Modules (`agx/`)

- **`core.py`** — Main orchestrator. Runs the full pipeline with bounded retry (max 3 attempts). Entry point: `agx_main(prompt, max_retries)`.
- **`distill.py`** — Two-pass LLM pruning. Pass 1 selects AWS service groups, Pass 2 selects specific resource types. Max 20 resources.
- **`function_builder.py`** — Generates Python functions dynamically from Terraform resource schemas. Each function takes a label + attributes and returns HCL. Also builds the prompt fragment listing available functions.
- **`planner.py`** — Sends prompt to LLM, extracts first JSON array from response. Plan format: `[{function, args, assign?}, ...]`.
- **`validate_plan.py`** — Validates plans structurally: function existence, parameter names/types, required params, variable-before-assignment, return type hints.
- **`dag.py`** — DAG construction (Kahn's algorithm) from `aws_dependency_map.json`. Validates topological ordering and dependency completeness in plans.
- **`compiler.py`** — Converts validated plan JSON into executable Python script. Inserts function source code, builds `main()` with variable assignments and f-string interpolation.
- **`llm_openai.py`** — OpenAI API wrapper. Uses `gpt-4.1-nano`. Provides `generate_raw_json()` for planning (with retry feedback) and `call_llm()` for distillation.

### Data Files

- **`agx/tf_schema/aws_resource_tree.json`** — Compressed AWS resource schemas (469 lines) organized by service group with required/optional attributes.
- **`agx/tf_schema/aws_dependency_map.json`** — Hand-curated resource dependency map for DAG validation.
- **`agx/tf_schema/build_tree.py`** — Utility to generate the resource tree from `terraform providers schema -json` output.
- **`agx/prompt_templates/`** — LLM prompt templates for planning (`devops_test.txt`) and distillation passes (`distill_pass1.txt`, `distill_pass2.txt`).

### Registries

- **`agx/registries/devops_test.py`** — Static demo registry (S3 bucket functions). Used as fallback when dynamic registry isn't available.
- **`agx/registries/utilities.py`** — Utility functions included in every dynamic registry: `log_message`, `save_hcl_to_file`, `sanitise_resource_name`, `combine_hcl_blocks`.

### Backend (`agx_backend/`)

- **`app.py`** — FastAPI server. Single `POST /` endpoint calling `agx_main()`. Rate-limited to 5/day per IP via slowapi + Redis. CORS allows localhost:3000 and agx.run.

### Frontend (`agx_frontend/`)

- Next.js app (TypeScript). Single-page at `app/page.tsx`. Calls `/api` route which proxies to the FastAPI backend. Shows 3-step processing animation, code output with copy/download.

### Entry Points

- **CLI:** `python run.py` — loads `.env`, calls `agx_main()` interactively.
- **Backend:** FastAPI app in `agx_backend/app.py`. Deployed on Fly.io.
- **Frontend:** Next.js app. Deployed on Vercel.

## Development

### Requirements

- Python 3.11
- Dependencies: `pip install -r requirements.txt` (python-dotenv, fastapi, openai, slowapi, redis)
- Tests need: `pip install pytest`
- OpenAI API key in `.env` as `OPENAI_API_KEY`

### Running Tests

```bash
pytest agx/tests/ -v
```

Tests cover: compiler, core orchestrator, DAG, distillation, function builder, TF schema, and validate_plan. Tests mock LLM calls — no API key needed.

### CI

GitHub Actions runs `pytest agx/tests/ -v` on Python 3.11 for pushes/PRs to main and develop branches.

### Key Patterns

- Plan format: `[{"function": "name", "args": {...}, "assign": "var_name"}, ...]`
- Variable references use `{var_name}` syntax in string args, compiled to f-strings.
- Dynamic functions are named `create_{resource_type}` (e.g., `create_aws_s3_bucket`).
- Validation is structural (pre-execution), not semantic — catches wrong function names, bad params, missing deps, ordering violations.
