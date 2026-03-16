---
name: find-impacts
description: Find the impact radius of a planned change before edits. Use when Codex needs to determine what will be affected by a refactor, where a function or endpoint is used, what tests must change, or how schema, API, config, and deployment boundaries will ripple.
---

# Find Impacts

Map change impact before proposing edits.

Prefer search and grouping over early implementation.

## Workflow

1. Identify the exact target: symbol, endpoint, config key, DTO, table, migration, or file.
2. Use `rg` first to find:
   - definitions
   - direct references
   - tests
   - docs
   - config files
   - infra or deployment references
3. Group findings into:
   - direct callers
   - indirect dependencies
   - request and response contracts
   - persistence or schema impact
   - tests to update
   - deployment or runtime config impact
4. If the change crosses service or package boundaries, call out compatibility and rollout risks.

## Output

Return a concise impact report before proposing code changes.

Do not start editing until the impact report is complete unless the user explicitly asks for immediate edits.
