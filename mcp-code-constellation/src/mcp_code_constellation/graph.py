import networkx as nx
from typing import Dict, List, Any, Set

class ConstellationGraph:
    def __init__(self, nodes: Dict[str, Any], symbol_map: Dict[str, str]):
        self.nodes = nodes
        self.symbol_map = symbol_map
        self.G = nx.DiGraph()
        self._build()
        
    def _build(self):
        # Add all nodes
        for node_id, node_data in self.nodes.items():
            self.G.add_node(node_id, **node_data)
            
        # Add edges (Caller -> Callee)
        for node_id, node_data in self.nodes.items():
            calls = node_data.get("calls", [])
            for call_sym in calls:
                target_id = self.symbol_map.get(call_sym)
                if target_id and target_id in self.nodes:
                    # Both nodes exist in our parsed index
                    self.G.add_edge(node_id, target_id)
                    
    def get_flow(self, entry_node_id: str, max_depth: int = 3) -> List[Any]:
        """Get the full downstream flow from an entry node."""
        if entry_node_id not in self.G:
            return []
            
        # Traverse BFS or DFS up to max_depth
        edges = nx.bfs_edges(self.G, source=entry_node_id, depth_limit=max_depth)
        
        visited = {entry_node_id}
        for u, v in edges:
            visited.add(u)
            visited.add(v)
            
        return [self.nodes[n] for n in visited]
        
    def get_constellation(self, node_id: str, depth: int = 1) -> Dict[str, List[Any]]:
        """Get parents (callers) and children (callees) for a specific node."""
        if node_id not in self.G:
            return {"parents": [], "children": [], "node": None}
            
        # Children
        children_edges = nx.bfs_edges(self.G, source=node_id, depth_limit=depth)
        children = {v for u, v in children_edges}
        
        # Parents (reverse graph)
        rev_G = self.G.reverse(copy=False)
        parent_edges = nx.bfs_edges(rev_G, source=node_id, depth_limit=depth)
        parents = {v for u, v in parent_edges}
        
        return {
            "node": self.nodes[node_id],
            "parents": [self.nodes[p] for p in parents],
            "children": [self.nodes[c] for c in children]
        }
