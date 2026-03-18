import os
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import Dict, List, Any

class VectorStore:
    def __init__(self, cache_dir: str = ".constellation"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.nodes: Dict[str, Any] = {}
        
        # Init Chroma
        self.chroma_client = chromadb.PersistentClient(path=str(self.cache_dir))
        self.embed_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="constellation_nodes",
            embedding_function=self.embed_fn
        )
        
    def load(self) -> bool:
        # ChromaDB handles load automatically. Just check if we have data inside.
        if self.collection.count() > 0:
            # We can't entirely reconstruct `self.nodes` natively from just a count easily without fetching all, 
            # but we can fetch them if needed. 
            # For simplicity, we just fetch everything to populate self.nodes for graph building.
            all_data = self.collection.get()
            
            for i in range(len(all_data['ids'])):
                node_id = all_data['ids'][i]
                meta = all_data['metadatas'][i]
                # Reconstruct minimum node required by the rest of the app
                # We stored calls as a comma separated string
                calls = meta.get("calls", "").split(",") if meta.get("calls") else []
                self.nodes[node_id] = {
                    "id": node_id,
                    "name": meta["name"],
                    "type": meta["type"],
                    "file_path": meta["file_path"],
                    "source": all_data['documents'][i],
                    "calls": calls
                }
            return True
        return False
        
    def index_nodes(self, new_nodes: Dict[str, Any]):
        """Index a dictionary of nodes into ChromaDB."""
        self.nodes = new_nodes
        
        ids = []
        documents = []
        metadatas = []
        
        for k, v in self.nodes.items():
            ids.append(k)
            documents.append(v.get("source", ""))
            
            calls = v.get("calls", [])
            metadatas.append({
                "name": v.get("name", ""),
                "type": v.get("type", ""),
                "file_path": v.get("file_path", ""),
                "calls": ",".join(calls)
            })
            
        print(f"Generating FastEmbed embeddings for {len(ids)} nodes in ChromaDB...")
        
        # Clear existing
        if self.collection.count() > 0:
            self.chroma_client.delete_collection("constellation_nodes")
            self.collection = self.chroma_client.create_collection(
                name="constellation_nodes", 
                embedding_function=self.embed_fn
            )
            
        # Batch insert
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
        print("Indexing complete.")
        
    def search(self, query: str, top_k: int = 5) -> List[Any]:
        if self.collection.count() == 0:
            return []
            
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        ret = []
        if len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                node_id = results['ids'][0][i]
                score = results['distances'][0][i]
                ret.append({
                    "score": score,
                    "node": self.nodes[node_id]
                })
                
        return ret
