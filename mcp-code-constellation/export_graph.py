import os
import json
from pathlib import Path

# Add src to path so we can import our modules
import sys
sys.path.insert(0, str(Path("src").resolve()))

from mcp_code_constellation.storage import VectorStore

def clean_label(text):
    return text.replace('"', "'").replace("\n", " ")

def build_html():
    store = VectorStore(cache_dir=".constellation")
    store.load()
    
    nodes = store.nodes
    
    mermaid_lines = ["graph LR"]
    
    import hashlib
    def get_id(raw_id):
        return "node_" + hashlib.md5(raw_id.encode('utf-8')).hexdigest()[:10]
        
    # 1. Define nodes
    for k, v in nodes.items():
        node_id = get_id(v["id"])
        safe_name = clean_label(v.get("name", "Unknown"))
        
        # Color nodes by type
        if v.get("type") == "class":
            mermaid_lines.append(f'    {node_id}["{safe_name}"]:::classNode')
        else:
            mermaid_lines.append(f'    {node_id}["{safe_name}"]:::funcNode')
            
    # 2. Define edges
    # We need a reverse map from 'name' to 'id' since 'calls' only has the raw names
    sym_map = {v["name"]: k for k, v in nodes.items()}
    
    added_edges = set()
    for k, v in nodes.items():
        caller_id = get_id(v["id"])
        calls = v.get("calls", [])
        for call_name in calls:
            # If the call is an internal function we indexed
            if call_name in sym_map:
                callee_k = sym_map[call_name]
                callee_id = get_id(callee_k)
                
                edge_key = f"{caller_id}->{callee_id}"
                if edge_key not in added_edges:
                    mermaid_lines.append(f"    {caller_id} --> {callee_id}")
                    added_edges.add(edge_key)

    mermaid_lines.append("    classDef classNode fill:#2d3748,stroke:#63b3ed,stroke-width:2px,color:#fff;")
    mermaid_lines.append("    classDef funcNode fill:#1a202c,stroke:#9f7aea,stroke-width:2px,color:#fff;")
    
    mermaid_graph = "\\n".join(mermaid_lines)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Code Constellation Map</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f111a;
      --surface: #1a1d27;
      --border: rgba(255, 255, 255, 0.1);
      --text: #e2e8f0;
      --text-dim: #94a3b8;
      --accent1: #9f7aea; /* Purple for functions */
      --accent2: #63b3ed; /* Blue for classes */
    }}
    
    body {{
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Inter', system-ui, sans-serif;
      margin: 0;
      padding: 2rem;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    
    header {{
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1rem;
    }}
    
    h1 {{
      font-weight: 800;
      margin: 0 0 0.5rem 0;
      background: linear-gradient(135deg, var(--accent2), var(--accent1));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    
    p {{
      color: var(--text-dim);
      margin: 0;
    }}
    
    .legend {{
      display: flex;
      gap: 1rem;
      margin-top: 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
    }}
    
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    
    .dot {{
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }}
    .dot.func {{ background: var(--surface); border: 2px solid var(--accent1); }}
    .dot.cls {{ background: #2d3748; border: 2px solid var(--accent2); }}
    
    .mermaid-wrap {{
      flex: 1;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 2rem;
      overflow: auto;
      display: flex;
      justify-content: center;
      align-items: center;
      box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }}
  </style>
</head>
<body>
  <header>
    <h1>Code Constellation Map</h1>
    <p>Visualizing <strong>{len(nodes)}</strong> parsed components and their upstream/downstream call graphs.</p>
    <div class="legend">
      <div class="legend-item"><div class="dot func"></div> Function</div>
      <div class="legend-item"><div class="dot cls"></div> Class</div>
    </div>
  </header>
  
  <div class="mermaid-wrap">
    <div class="mermaid">
      {mermaid_graph}
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>
    mermaid.initialize({{ 
        startOnLoad: true, 
        theme: 'dark',
        fontFamily: 'JetBrains Mono'
    }});
  </script>
</body>
</html>
"""
    
    out_path = Path("constellation_map.html").resolve()
    out_path.write_text(html)
    print(f"Graph written to {out_path}")

if __name__ == "__main__":
    build_html()
