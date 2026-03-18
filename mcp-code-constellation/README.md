# 🌌 Code Constellation MCP Server

A real-time, local AST parser and Semantic Vector DB that maps your codebase and visually displays function call graphs, dependencies, and execution flows for Large Language Models.

This server provides precise tools to LLMs so they can navigate code structurally instead of blindly guessing file dependencies.

## Features
- **Tree-sitter Parsing**: Extracts functions and classes across Python, JS, and TS globally.
- **Local ChromaDB**: Generates ultra-fast semantic embeddings offline without OpenAI keys.
- **DAG Call Graphs**: Tracks exactly which functions call which functions mathematically.
- **Live Visualizer**: Automatically pops open a live `vis.js` constellation graph in your browser on MCP boot, synced directly to the codebase via smart Javascript polling!

## Server Tools
- `index_target_repo(absolute_path)`: Scans the repo, builds the DB, and live-updates the visualizer.
- `search_flow(query)`: Semantic search that returns full multi-file execution paths.
- `get_function_constellation(symbol)`: Returns immediate upstream/downstream callers.
- `open_visualizer()`: Manually forces the browser visualizer to pop open.

---

## 🤖 The Master System Prompt

To ensure your AI agent uses this server effectively, you **must** paste the following rules into your agent's system instructions (e.g. `.cursorrules`, `GEMINI.md`, or Custom Instructions).

```markdown
# 🌌 Code Constellation Protocol

You have access to the Code Constellation MCP Server. This is your primary mechanism for understanding the semantic topography and cross-file dependencies of this repository. You MUST adhere to the following execution protocols without exception:

1. **Pre-Execution Reconnaissance**: Before proposing any architectural plans or modifying any files, use `@mcp:code-constellation:search_flow` or `get_function_constellation` to retrieve the upstream and downstream call graph.
2. **Structural Awareness**: Do not blindly `grep` or read full files randomly if you are trying to understand a feature's boundary; rely on the Code Constellation graph tools.
3. **Mandatory Dynamic Re-Indexing**: Every single time you finish an implementation step or modify a file, you MUST immediately call `@mcp:code-constellation:index_target_repo`. Do this proactively to ensure the downstream semantic cache and the user's live Graph Visualizer never slip out of sync.
```

---

## 🚀 Client Setup Guides

### 1. Cursor
Create a `.cursorrules` file in the root of your project and paste the **Master System Prompt** above into it. Cursor will automatically read this before every generation.
For the MCP server itself, add it in `Cursor Settings -> Features -> MCP`:
- Type: `command`
- Command: `uv run python /absolute/path/to/mcp-code-constellation/src/mcp_code_constellation/server.py`

### 2. Antigravity / Gemini
Gemini/Antigravity natively utilizes `mcp_config.json` and `.gemini/GEMINI.md`.
1. Paste the **Master System Prompt** into your `.gemini/GEMINI.md` file.
2. Add the server to `~/.gemini/antigravity/mcp_config.json`:
```json
{
  "mcpServers": {
    "code-constellation": {
      "command": "uv",
      "args": ["run", "python", "src/mcp_code_constellation/server.py"],
      "env": {
        "PYTHONPATH": "src"
      },
      "directory": "/absolute/path/to/mcp-code-constellation"
    }
  }
}
```

### 3. Claude Desktop
Add the server to your `claude_desktop_config.json` (usually located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "code-constellation": {
      "command": "uv",
      "args": ["run", "python", "/absolute/path/to/mcp-code-constellation/src/mcp_code_constellation/server.py"],
      "env": { "PYTHONPATH": "src" }
    }
  }
}
```
*Note: You can paste the Master System Prompt into Claude's "Project Knowledge" panel if using Claude Projects.*

### 4. Serena / Codex (`config.toml`)
Serena and Codex use standard MCP entries in `config.toml`.
1. Add the server to `~/.codex/config.toml` for a global setup, or to `.codex/config.toml` inside a specific repo for a project-scoped setup:
```toml
[mcp_servers.code-constellation]
command = "uv"
args = [
  "--directory", "/absolute/path/to/mcp-code-constellation",
  "run", "python", "src/mcp_code_constellation/server.py"
]

startup_timeout_sec = 20
tool_timeout_sec = 120
```
2. Paste the **Master System Prompt** directly into your Serena agent instructions, Codex `AGENTS.md`, or another system-instructions file that your client reads automatically.
3. Restart the client after saving `config.toml` so it reloads the MCP server list.
