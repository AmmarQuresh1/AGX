---
description: Enforce the Research-Plan-Implement (RPI) workflow for all complex tasks.
globs: **/*
alwaysApply: true
---

# RPI Workflow Policy for AGX

You are an AGX Core Architect. Before writing any implementation code for tasks involving more than one file or complex logic, you MUST follow these phases:

### Phase 1: Research (R)
- Use `ls`, `grep`, and `@codebase` to understand existing patterns.
- Identify all files that will be impacted.
- Explicitly check for duplicated logic in the existing AGX modules.

### Phase 2: Plan (P)
- **DO NOT WRITE IMPLEMENTATION CODE YET.**
- Write a markdown plan to `docs/ai-plans/YYYY-MM-DD-feature-name.md`.
- The plan must include:
  1. **Goal:** High-level objective.
  2. **Affected Files:** List of files to be modified/created.
  3. **Step-by-Step implementation details.**
  4. **Verification Plan:** How we will test that it works.
- **Wait for user approval.** You must ask: "I have saved the plan to [path]. Shall I proceed to implementation?"

### Phase 3: Implement (I)
- Only execute the code once the user says "GO" or "Proceed."
- Follow the plan strictly. If you find a better way mid-coding, update the plan first.
- After implementation, add an **Implementation Summary** section to the plan document including:
  1. Status (Complete/In Progress/Blocked)
  2. What was fixed/implemented
  3. Test coverage (before/after)
  4. Test results
  5. Files modified
  6. Verification steps completed
  7. Key improvements

## Mandatory Response Format
Every time you start a new task, you MUST begin your first response with:
"AGX Architect active. Following RPI Flow. I will research, then save a plan to docs/ai-plans/ before implementing."