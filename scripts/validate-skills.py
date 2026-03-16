#!/usr/bin/env python3
import re
import sys
from pathlib import Path

import yaml

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_FRONTMATTER_KEYS = {"name", "description"}


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---\n"):
        raise ValueError("No YAML frontmatter found")

    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        raise ValueError("Invalid frontmatter format")

    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML mapping")
    return data


def validate_skill(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"{skill_dir}: missing SKILL.md")

    frontmatter = parse_frontmatter(skill_md.read_text())

    unexpected = sorted(set(frontmatter) - ALLOWED_FRONTMATTER_KEYS)
    if unexpected:
        raise ValueError(f"{skill_dir}: unexpected frontmatter keys: {', '.join(unexpected)}")

    for key in ("name", "description"):
        value = frontmatter.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{skill_dir}: missing or invalid {key!r}")

    name = frontmatter["name"].strip()
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise ValueError(f"{skill_dir}: skill name must be lowercase hyphen-case")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        raise ValueError(f"{skill_dir}: skill name cannot start/end with '-' or contain '--'")
    if len(name) > MAX_SKILL_NAME_LENGTH:
        raise ValueError(f"{skill_dir}: skill name exceeds {MAX_SKILL_NAME_LENGTH} characters")

    description = frontmatter["description"].strip()
    if len(description) > 1024:
        raise ValueError(f"{skill_dir}: description exceeds 1024 characters")
    if "<" in description or ">" in description:
        raise ValueError(f"{skill_dir}: description cannot contain angle brackets")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: validate-skills.py <skill-dir> [<skill-dir> ...]", file=sys.stderr)
        return 1

    for raw_path in argv[1:]:
        skill_dir = Path(raw_path)
        validate_skill(skill_dir)
        print(f"ok {skill_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
