## Codex workflow
- Use `$repo-map` before explaining the codebase, identifying entry points, or locating a feature.
- Use `$find-impacts` before non-trivial edits, refactors, schema changes, API changes, or config changes.
- Prefer `rg`, `fd`, `git diff`, and `scripts/ai/repo-map.sh` over opening many files.
- Read the minimum required files before editing.
- When a task depends on OpenAI product behavior, prefer the OpenAI developer docs MCP server.

