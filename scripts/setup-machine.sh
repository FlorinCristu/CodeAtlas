#!/usr/bin/env bash
set -euo pipefail

with_context7=0
with_openai_docs=0
skip_tools=0

usage() {
  cat <<'EOF'
Usage: ./scripts/setup-machine.sh [--with-context7] [--with-openai-docs] [--skip-tools]

Installs:
  - @openai/codex
  - ripgrep
  - fd
  - tree-sitter-cli

Optional:
  --with-context7       Add the Context7 MCP server
  --with-openai-docs    Add the OpenAI Developer Docs MCP server
  --skip-tools          Skip ripgrep/fd/tree-sitter installation
EOF
}

have() {
  command -v "$1" >/dev/null 2>&1
}

log_info() {
  printf '%s\n' "$1"
}

run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
    return
  fi

  if have sudo; then
    sudo "$@"
    return
  fi

  printf 'Need root access or sudo to install system packages.\n' >&2
  exit 1
}

detect_package_manager() {
  if have brew; then
    printf 'brew\n'
    return
  fi
  if have apt-get; then
    printf 'apt-get\n'
    return
  fi
  if have dnf; then
    printf 'dnf\n'
    return
  fi
  if have pacman; then
    printf 'pacman\n'
    return
  fi

  printf 'No supported package manager found. Install ripgrep and fd manually.\n' >&2
  exit 1
}

install_system_packages() {
  local manager
  manager="$(detect_package_manager)"

  if [[ "$#" -eq 0 ]]; then
    return
  fi

  case "$manager" in
    brew)
      brew install "$@"
      ;;
    apt-get)
      run_root apt-get update
      run_root apt-get install -y "$@"
      ;;
    dnf)
      run_root dnf install -y "$@"
      ;;
    pacman)
      run_root pacman -Sy --noconfirm "$@"
      ;;
  esac
}

ensure_fd_alias() {
  if have fd; then
    return
  fi

  if ! have fdfind; then
    return
  fi

  mkdir -p "$HOME/.local/bin"
  ln -sf "$(command -v fdfind)" "$HOME/.local/bin/fd"

  case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *)
      printf 'Created %s/.local/bin/fd. Add %s/.local/bin to PATH if fd is still not found.\n' "$HOME" "$HOME"
      ;;
  esac
}

ensure_search_tools() {
  local manager
  local packages=()

  if [[ "$skip_tools" -eq 1 ]]; then
    log_info 'Skipping ripgrep/fd installation.'
    return
  fi

  manager="$(detect_package_manager)"

  if ! have rg; then
    packages+=("ripgrep")
  fi

  if ! have fd && ! have fdfind; then
    case "$manager" in
      apt-get|dnf)
        packages+=("fd-find")
        ;;
      *)
        packages+=("fd")
        ;;
    esac
  fi

  install_system_packages "${packages[@]}"
  ensure_fd_alias
}

require_npm() {
  if have npm; then
    return
  fi

  printf 'npm is required. Install Node.js and npm first, then rerun this script.\n' >&2
  exit 1
}

ensure_codex() {
  if have codex; then
    log_info "Codex already installed: $(codex --version)"
    return
  fi

  require_npm
  log_info 'Installing Codex CLI.'
  npm install -g @openai/codex@latest
  hash -r
}

ensure_tree_sitter() {
  if have tree-sitter; then
    log_info "tree-sitter already installed: $(tree-sitter --version)"
    return
  fi

  if [[ "$skip_tools" -eq 1 ]]; then
    log_info 'Skipping tree-sitter installation.'
    return
  fi

  require_npm

  log_info 'Installing tree-sitter-cli via npm.'
  if npm install -g tree-sitter-cli; then
    hash -r
    return
  fi

  if have cargo; then
    log_info 'Retrying tree-sitter-cli via cargo.'
    cargo install --locked tree-sitter-cli
    hash -r
    return
  fi

  printf 'tree-sitter-cli install failed via npm and cargo is not available.\n' >&2
  exit 1
}

get_mcp_server_json() {
  local name="$1"
  codex mcp get "$name" --json 2>/dev/null
}

mcp_server_matches_stdio() {
  local name="$1"
  local command_name="$2"
  local current_json

  if ! current_json="$(get_mcp_server_json "$name")"; then
    return 1
  fi

  printf '%s' "$current_json" | grep -F '"enabled": true' >/dev/null &&
    printf '%s' "$current_json" | grep -F '"type": "stdio"' >/dev/null &&
    printf '%s' "$current_json" | grep -F "\"command\": \"$command_name\"" >/dev/null &&
    printf '%s' "$current_json" | grep -F '"-y"' >/dev/null &&
    printf '%s' "$current_json" | grep -F '"@upstash/context7-mcp"' >/dev/null
}

mcp_server_matches_http() {
  local name="$1"
  local url="$2"
  local current_json

  if ! current_json="$(get_mcp_server_json "$name")"; then
    return 1
  fi

  printf '%s' "$current_json" | grep -F '"enabled": true' >/dev/null &&
    printf '%s' "$current_json" | grep -F '"type": "streamable_http"' >/dev/null &&
    printf '%s' "$current_json" | grep -F "\"url\": \"$url\"" >/dev/null
}

ensure_mcp_stdio_server() {
  local name="$1"
  local command_name="$2"
  shift 2
  local add_args=("$@")

  if mcp_server_matches_stdio "$name" "$command_name"; then
    log_info "MCP server '$name' already configured."
    return
  fi

  if get_mcp_server_json "$name" >/dev/null; then
    log_info "MCP server '$name' exists with different settings. Updating."
    codex mcp remove "$name" >/dev/null
  else
    log_info "Adding MCP server '$name'."
  fi

  codex mcp add "$name" -- "${add_args[@]}" >/dev/null
}

ensure_mcp_http_server() {
  local name="$1"
  local url="$2"

  if mcp_server_matches_http "$name" "$url"; then
    log_info "MCP server '$name' already configured."
    return
  fi

  if get_mcp_server_json "$name" >/dev/null; then
    log_info "MCP server '$name' exists with different settings. Updating."
    codex mcp remove "$name" >/dev/null
  else
    log_info "Adding MCP server '$name'."
  fi

  codex mcp add "$name" --url "$url" >/dev/null
}

configure_mcp_servers() {
  if [[ "$with_context7" -eq 0 && "$with_openai_docs" -eq 0 ]]; then
    return
  fi

  ensure_codex

  if [[ "$with_context7" -eq 1 ]]; then
    ensure_mcp_stdio_server context7 npx npx -y @upstash/context7-mcp
  fi

  if [[ "$with_openai_docs" -eq 1 ]]; then
    ensure_mcp_http_server openaiDeveloperDocs https://developers.openai.com/mcp
  fi
}

print_summary() {
  printf '\nInstalled tools:\n'
  have codex && printf '  codex: %s\n' "$(codex --version)"
  have rg && printf '  rg: %s\n' "$(rg --version | head -n 1)"
  if have fd; then
    printf '  fd: %s\n' "$(fd --version)"
  elif have fdfind; then
    printf '  fdfind: %s\n' "$(fdfind --version)"
  fi
  have tree-sitter && printf '  tree-sitter: %s\n' "$(tree-sitter --version)"
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --with-context7)
      with_context7=1
      ;;
    --with-openai-docs)
      with_openai_docs=1
      ;;
    --skip-tools)
      skip_tools=1
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

ensure_search_tools
ensure_codex
ensure_tree_sitter
configure_mcp_servers
print_summary

printf '\nMachine setup complete.\n'
