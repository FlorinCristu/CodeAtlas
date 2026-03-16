# Codex Starter Kit

Portable starter repo for a lean Codex workflow:

- machine setup for `codex`, `rg`, `fd`, and `tree-sitter`
- project bootstrap for `.codex`, `.agents/skills`, `AGENTS.md`, and `scripts/ai`
- two narrow skills that keep Codex in an `understand -> impact -> edit` loop

The OpenAI-specific pieces in this repo were verified on March 16, 2026 against the official docs and the live CLI:

- [Codex CLI](https://developers.openai.com/codex/cli)
- [Config basics](https://developers.openai.com/codex/config)
- [Skills](https://developers.openai.com/codex/skills)
- [AGENTS.md](https://developers.openai.com/codex/agents)
- [MCP](https://developers.openai.com/codex/mcp)
- [Developer Docs MCP](https://developers.openai.com/mcp)

## What this repo installs into a target project

- `.codex/config.toml`
- `.agents/skills/repo-map/SKILL.md`
- `.agents/skills/find-impacts/SKILL.md`
- `AGENTS.md` starter block
- `.gitignore` starter block
- `scripts/ai/repo-map.sh`

## Quick start

Clone this repo, then run the machine bootstrap once per machine:

```bash
./scripts/setup-machine.sh
```

Rerunning it is safe. Existing MCP servers are now reported as `already configured`, and mismatched ones are updated in place.

Add optional MCP servers when you want external docs:

```bash
./scripts/setup-machine.sh --with-context7 --with-openai-docs
```

Bootstrap any target repo:

```bash
./scripts/bootstrap-project.sh --target /path/to/your/project
```

Safer modes:

```bash
./scripts/bootstrap-project.sh --target /path/to/your/project --dry-run
./scripts/bootstrap-project.sh --target /path/to/your/project --update-only
./scripts/bootstrap-project.sh --target /path/to/your/project --force
```

- `--dry-run` previews writes, updates, and skips without changing files
- `--update-only` refreshes only existing managed files or managed blocks
- `--force` replaces existing managed files and refreshes managed blocks

## Workflow

Start Codex from the target repo root:

```bash
codex
```

Then use a strict two-step loop:

```text
Use $repo-map and explain this codebase. Do not edit anything yet.
Use $find-impacts for the change I want to make. Do not edit anything until the impact report is done.
```

## Publish and share

This repo keeps the skills in `skills/` so other users can install them directly from GitHub with the built-in `$skill-installer` skill after you publish the repo.

Examples after publishing:

```text
Use $skill-installer to install https://github.com/<owner>/<repo>/tree/main/skills/repo-map
Use $skill-installer to install https://github.com/<owner>/<repo>/tree/main/skills/find-impacts
```

Or point people at the repo-level bootstrap:

```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
./scripts/setup-machine.sh --with-context7 --with-openai-docs
./scripts/bootstrap-project.sh --target /path/to/project
```

## CI

GitHub Actions validation lives in `.github/workflows/validate.yml` and checks:

- shell syntax
- `SKILL.md` frontmatter validity
- bootstrap behavior, including `--dry-run` and `--update-only`
- MCP setup idempotence and mismatch repair

## Scope

- macOS and Linux are supported directly
- Windows should use WSL2, which matches the current Codex CLI docs
- project config stays minimal on purpose; repo-specific behavior belongs in `AGENTS.md` and `.agents/skills/`
