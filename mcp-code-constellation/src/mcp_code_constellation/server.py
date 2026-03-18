import anyio
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from pathlib import os
import threading
import webbrowser
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Import our custom logic
from mcp_code_constellation.indexer import CodeAtlasIndexer
from mcp_code_constellation.storage import VectorStore
from mcp_code_constellation.graph import ConstellationGraph
from mcp_code_constellation import web_visualizer

mcp = FastMCP("code_constellation")

# Global instances (init on startup if index exists)
storage = VectorStore()
graph: Optional[ConstellationGraph] = None
is_indexed = storage.load()

# Rebuild graph if loaded from cache
if is_indexed:
    # Need symbol map. The current cache doesn't store symbol map!
    # Let's rebuild symbol map quickly from loaded nodes
    sym_map = {n["name"]: k for k, n in storage.nodes.items()}
    graph = ConstellationGraph(storage.nodes, sym_map)

# ---- Start Background Visualizer & Open Browser ----
def start_web_server():
    # Attempt to run web_visualizer, suppress print statements from httpd if needed
    try:
        web_visualizer.run()
    except Exception:
        pass

viz_thread = threading.Thread(target=start_web_server, daemon=True)
viz_thread.start()

# Pop open the visualizer on boot (Serena behavior)
try:
    webbrowser.open("http://localhost:8080/")
except Exception:
    pass
# ----------------------------------------------------

@mcp.tool()
def index_target_repo(absolute_path: str) -> str:
    """
    Index a given repository using Tree-sitter and embeddings. This can take a few minutes for large codebases.
    CRITICAL INSTRUCTION: Agents MUST call this tool every time they finish an implementation or modify the codebase!
    """
    global graph, is_indexed
    
    idx = CodeAtlasIndexer(absolute_path)
    nodes = idx.build()
    
    if not nodes:
        return f"Found no parsable functions or classes in {absolute_path}."
        
    storage.index_nodes(nodes)
    graph = ConstellationGraph(storage.nodes, idx.symbol_map)
    is_indexed = True
    
    return f"Successfully indexed {len(nodes)} semantic nodes across the repository."

@mcp.tool()
def open_visualizer() -> str:
    """
    Open the live Code Constellation visualizer in the default web browser.
    """
    try:
        webbrowser.open("http://localhost:8080/")
        return "Successfully opened the visualizer in your browser."
    except Exception as e:
        return f"Failed to open browser: {e}"

@mcp.tool()
def search_flow(query: str, depth: int = 3) -> str:
    """Search for a codebase flow (e.g. 'Authentication', 'Create Order') and return the fully resolved Call Graph constellation of functions for the LLM to understand."""
    if not is_indexed or not graph:
        return "The repository has not been indexed yet. Call `index_target_repo` first."
        
    # 1. Semantic search to find the entry node
    results = storage.search(query, top_k=1)
    if not results:
        return "No matching elements found."
        
    entry_node = results[0]["node"]
    entry_id = entry_node["id"]
    
    # 2. Traverse the graph down `depth` levels
    flow_nodes = graph.get_flow(entry_id, max_depth=depth)
    
    # 3. Format as a comprehensive summary
    markdown = f"## 🌌 Flow Constellation for: '{query}'\n"
    markdown += f"**Entry Point:** `{entry_node['name']}` (Score: {results[0]['score']:.2f})\n"
    markdown += f"**Total Flow Context Nodes:** {len(flow_nodes)}\n\n"
    
    for n in flow_nodes:
        markdown += f"### {n['type'].capitalize()}: {n['name']}\n"
        markdown += f"- **File:** `{n['file_path']}`\n"
        markdown += f"- **Calls Downstream:** {', '.join(n['calls']) if n.get('calls') else 'None'}\n"
        markdown += f"```python\n{n['source']}\n```\n\n"
        
    return markdown

@mcp.tool()
def get_function_constellation(symbol_name: str, depth: int = 1) -> str:
    """Get the upstream (callers) and downstream (callees) for an exact function name."""
    if not is_indexed or not graph:
        return "The repository has not been indexed yet. Call `index_target_repo` first."
        
    # Find matching node id
    target_id = None
    for k, v in storage.nodes.items():
        if v["name"] == symbol_name:
            target_id = k
            break
            
    if not target_id:
        return f"Could not find exact symbol '{symbol_name}' in the index."
        
    const_data = graph.get_constellation(target_id, depth)
    
    markdown = f"## 🌌 Constellation for Symbol `{symbol_name}`\n\n"
    
    parents = const_data["parents"]
    children = const_data["children"]
    
    markdown += f"### ⬆️ Upstream Callers ({len(parents)})\n"
    for p in parents:
        markdown += f"- `{p['name']}` (File: `{p['file_path']}`)\n"
        
    markdown += f"\n### 🎯 Target: `{symbol_name}`\n"
    markdown += f"```\n{const_data['node']['source']}\n```\n"
    
    markdown += f"\n### ⬇️ Downstream Callees ({len(children)})\n"
    for c in children:
        markdown += f"#### `{c['name']}` (File: `{c['file_path']}`)\n"
        markdown += f"```\n{c['source']}\n```\n"
        
    return markdown

def main():
    mcp.run()
    
if __name__ == "__main__":
    main()
