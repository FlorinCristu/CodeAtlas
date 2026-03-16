---
name: repo-map
description: Build a concise repository map before edits. Use when Codex needs to explain a codebase, summarize project structure, identify entry points, locate major modules, find where a feature lives, or narrow a large repo before proposing changes.
---

# Repo Map

Build the smallest useful map of the repository before making conclusions.

Prefer local discovery over reading full files.

## Workflow

1. Identify the project type from top-level signals such as `go.mod`, `package.json`, `pyproject.toml`, `Cargo.toml`, Gradle files, Maven files, Docker files, and `README.md`.
2. If `scripts/ai/repo-map.sh` exists at the repo root, run it before opening many files.
3. Use `fd` and `rg` first to find:
   - likely entry points
   - routes and handlers
   - service or use-case layers
   - repositories, DAOs, or persistence adapters
   - config files
   - tests
4. Read only the files required to confirm the structure.
5. If the repo is a monorepo, identify the relevant package or service boundary before drilling deeper.

## Output

Return a compact report with:

- project type
- likely entry points
- major modules
- config locations
- test locations
- likely hotspots for the requested task

Keep the answer structured and brief.
Do not dump long file contents unless the user asks.
