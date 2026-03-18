import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path("src").resolve()))
from mcp_code_constellation.storage import VectorStore

PORT = 8080

class ConstellationHandler(BaseHTTPRequestHandler):
    store = None
    
    def do_GET(self):
        if self.path == "/api/graph":
            self._serve_graph_api()
        else:
            self._serve_index()
            
    def _serve_graph_api(self):
        if ConstellationHandler.store is None:
            ConstellationHandler.store = VectorStore(cache_dir=".constellation")
        
        try:
            # Refresh collection reference locally because the Indexer completely deletes and recreates collections
            ConstellationHandler.store.collection = ConstellationHandler.store.chroma_client.get_collection("constellation_nodes")
            
            # Force a fresh load from the local Chroma database
            ConstellationHandler.store.nodes = {}
            ConstellationHandler.store.load()
        except Exception as e:
            # Race condition: Index is actively dropping/recreating the collection. Tell client to poll again later.
            self.send_response(503)
            self.end_headers()
            return
            
        nodes_dict = ConstellationHandler.store.nodes
        sym_map = {v["name"]: k for k, v in nodes_dict.items()}
        
        vis_nodes = []
        vis_edges = []
        
        for k, v in nodes_dict.items():
            vis_nodes.append({
                "id": k,
                "label": v.get("name", "Unknown"),
                "group": v.get("type", "function"),
                "title": f"File: {v.get('file_path')}"
            })
            
            calls = v.get("calls", [])
            for call_name in calls:
                if call_name in sym_map:
                    callee_k = sym_map[call_name]
                    vis_edges.append({
                        "from": k,
                        "to": callee_k,
                        "arrows": "to"
                    })
                    
        payload = {"nodes": vis_nodes, "edges": vis_edges}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def _serve_index(self):
        html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Live Code Constellation</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #0f111a;
      color: #e2e8f0;
      font-family: 'Inter', system-ui, sans-serif;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    header {
      padding: 1.5rem;
      background: #1a1d27;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-shrink: 0;
    }
    h1 { margin: 0; font-size: 1.5rem; color: #63b3ed; }
    #mynetwork {
      flex: 1;
      width: 100%;
      height: 100%;
      background: var(--bg);
      position: relative;
    }
  </style>
</head>
<body>
  <header>
    <h1>🌌 Code Constellation Visualizer</h1>
    <div id="stats">Loading graph data...</div>
  </header>
  <div id="mynetwork"></div>

  <script>
    let currentCount = -1;
    let myNetwork = null;
    let graphData = null;
    const container = document.getElementById('mynetwork');

    function fetchAndRender() {
      fetch('/api/graph')
        .then(r => r.json())
        .then(data => {
          // Only re-render if the node count fundamentally changes to avoid physics thrashing
          if (data.nodes.length !== currentCount) {
            currentCount = data.nodes.length;
            document.getElementById('stats').innerText = `${data.nodes.length} Nodes | ${data.edges.length} Edges`;
            
            if (!myNetwork) {
                // Initialize for the first time
                graphData = {
                  nodes: new vis.DataSet(data.nodes),
                  edges: new vis.DataSet(data.edges)
                };
                
                const options = {
                  nodes: {
                    shape: 'box',
                    margin: 10,
                    font: { color: '#ffffff', face: 'monospace' },
                    borderWidth: 2
                  },
                  edges: {
                    color: '#4db8ff',
                    smooth: { type: 'cubicBezier' }
                  },
                  groups: {
                    'function': { color: { background: '#2b6cb0', border: '#63b3ed' } },
                    'class': { color: { background: '#553c9a', border: '#9f7aea' } }
                  },
                  physics: {
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                      gravitationalConstant: -50,
                      centralGravity: 0.01,
                      springLength: 100,
                      springConstant: 0.08
                    }
                  }
                };
                myNetwork = new vis.Network(container, graphData, options);
            } else {
                // Hot update the existing dataset so it animates beautifully
                graphData.nodes.clear();
                graphData.edges.clear();
                graphData.nodes.add(data.nodes);
                graphData.edges.add(data.edges);
            }
          }
        })
        .catch(e => {
          document.getElementById('stats').innerText = "Disconnected. Retrying...";
        });
    }

    // Initial load
    fetchAndRender();
    
    // Live syncing via JS polling every 2.5 seconds (effectively WebSocket behavior with 0 dependencies)
    setInterval(fetchAndRender, 2500);
  </script>
</body>
</html>"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

def run():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ConstellationHandler)
    print(f"\\n🚀 Live Visualizer running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    run()
