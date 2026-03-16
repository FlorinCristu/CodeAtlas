#!/usr/bin/env bash
set -euo pipefail

target_dir='.'
force=0
dry_run=0
update_only=0

usage() {
  cat <<'EOF'
Usage: ./scripts/bootstrap-project.sh [--target PATH] [--force] [--dry-run] [--update-only]

Creates or updates a target project with:
  - .codex/config.toml
  - .agents/skills/repo-map
  - .agents/skills/find-impacts
  - AGENTS.md starter block
  - .gitignore starter block
  - scripts/ai/repo-map.sh

Options:
  --force        Replace existing managed files and refresh managed blocks
  --dry-run      Show planned actions without writing changes
  --update-only  Refresh only existing managed files or managed blocks; do not create missing files
EOF
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --target)
      shift
      if [[ "$#" -eq 0 ]]; then
        printf '--target requires a path.\n' >&2
        exit 1
      fi
      target_dir="$1"
      ;;
    --force)
      force=1
      ;;
    --dry-run)
      dry_run=1
      ;;
    --update-only)
      update_only=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n\n' "$1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

if [[ "$force" -eq 1 && "$update_only" -eq 1 ]]; then
  printf '%s\n' '--force and --update-only cannot be used together.' >&2
  exit 1
fi

case "$target_dir" in
  /*) ;;
  *) target_dir="$PWD/$target_dir" ;;
esac

print_action() {
  local verb="$1"
  local path="$2"
  local reason="${3:-}"
  local prefix=''

  if [[ "$dry_run" -eq 1 ]]; then
    prefix='would '
  fi

  if [[ -n "$reason" ]]; then
    printf '%s%s %s (%s)\n' "$prefix" "$verb" "$path" "$reason"
    return
  fi

  printf '%s%s %s\n' "$prefix" "$verb" "$path"
}

replace_block() {
  local destination="$1"
  local marker_begin="$2"
  local marker_end="$3"
  local block_file="$4"
  local temp_file

  temp_file="$(mktemp)"

  awk -v marker_begin="$marker_begin" -v marker_end="$marker_end" -v block_file="$block_file" '
    BEGIN {
      while ((getline line < block_file) > 0) {
        block = block line ORS
      }
      close(block_file)
      in_block = 0
    }
    index($0, marker_begin) {
      print marker_begin
      printf "%s", block
      print marker_end
      in_block = 1
      next
    }
    index($0, marker_end) {
      in_block = 0
      next
    }
    !in_block {
      print
    }
  ' "$destination" > "$temp_file"

  mv "$temp_file" "$destination"
}

copy_file() {
  local source="$1"
  local destination="$2"
  local action='write'

  if [[ -e "$destination" ]]; then
    if [[ "$force" -eq 1 || "$update_only" -eq 1 ]]; then
      action='update'
    else
      print_action 'skip' "$destination" 'already exists'
      return
    fi
  elif [[ "$update_only" -eq 1 ]]; then
    print_action 'skip' "$destination" 'missing and update-only'
    return
  fi

  print_action "$action" "$destination"
  if [[ "$dry_run" -eq 1 ]]; then
    return
  fi

  mkdir -p "$(dirname "$destination")"
  cp "$source" "$destination"
  if [[ "$destination" == *.sh ]]; then
    chmod +x "$destination"
  fi
}

copy_dir() {
  local source="$1"
  local destination="$2"
  local action='write'

  if [[ -e "$destination" ]]; then
    if [[ "$force" -eq 1 || "$update_only" -eq 1 ]]; then
      action='update'
    else
      print_action 'skip' "$destination" 'already exists'
      return
    fi
  elif [[ "$update_only" -eq 1 ]]; then
    print_action 'skip' "$destination" 'missing and update-only'
    return
  fi

  print_action "$action" "$destination"
  if [[ "$dry_run" -eq 1 ]]; then
    return
  fi

  mkdir -p "$(dirname "$destination")"
  if [[ -e "$destination" ]]; then
    rm -rf "$destination"
  fi

  cp -R "$source" "$destination"
}

append_block_if_missing() {
  local destination="$1"
  local marker_begin="$2"
  local marker_end="$3"
  local block_file="$4"

  if [[ -f "$destination" ]] && grep -Fq "$marker_begin" "$destination"; then
    if [[ "$force" -eq 1 || "$update_only" -eq 1 ]]; then
      print_action 'update' "$destination" 'managed block'
      if [[ "$dry_run" -eq 1 ]]; then
        return
      fi
      replace_block "$destination" "$marker_begin" "$marker_end" "$block_file"
    else
      print_action 'skip' "$destination" 'starter block already present'
    fi
    return
  fi

  if [[ "$update_only" -eq 1 ]]; then
    if [[ -f "$destination" ]]; then
      print_action 'skip' "$destination" 'no managed block and update-only'
    else
      print_action 'skip' "$destination" 'missing and update-only'
    fi
    return
  fi

  print_action 'update' "$destination" 'append managed block'
  if [[ "$dry_run" -eq 1 ]]; then
    return
  fi

  mkdir -p "$(dirname "$destination")"
  if [[ ! -f "$destination" ]]; then
    : > "$destination"
  fi

  if [[ -s "$destination" ]]; then
    printf '\n' >> "$destination"
  fi

  {
    printf '%s\n' "$marker_begin"
    cat "$block_file"
    printf '%s\n' "$marker_end"
  } >> "$destination"
}

copy_file "$repo_root/templates/project/.codex/config.toml" "$target_dir/.codex/config.toml"
copy_file "$repo_root/templates/project/scripts/ai/repo-map.sh" "$target_dir/scripts/ai/repo-map.sh"
copy_dir "$repo_root/skills/repo-map" "$target_dir/.agents/skills/repo-map"
copy_dir "$repo_root/skills/find-impacts" "$target_dir/.agents/skills/find-impacts"

append_block_if_missing \
  "$target_dir/AGENTS.md" \
  '<!-- codex-starter:begin -->' \
  '<!-- codex-starter:end -->' \
  "$repo_root/templates/project/AGENTS.md"

append_block_if_missing \
  "$target_dir/.gitignore" \
  '# codex-starter:begin' \
  '# codex-starter:end' \
  "$repo_root/templates/project/.gitignore.snippet"

printf '\nBootstrap complete for %s\n' "$target_dir"
