import os
import json
import numpy as np
import tree_sitter
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_kotlin
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class CodeNode:
    id: str
    name: str
    type: str # "function", "class", "method"
    file_path: str
    start_byte: int
    end_byte: int
    source: str
    calls: List[str] # List of function names it calls

class CodeAtlasIndexer:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()
        
        # Load languages
        self.langs = {
            ".py": tree_sitter.Language(tree_sitter_python.language()),
            ".js": tree_sitter.Language(tree_sitter_javascript.language()),
            ".jsx": tree_sitter.Language(tree_sitter_javascript.language()),
            ".ts": tree_sitter.Language(tree_sitter_typescript.language_typescript()),
            ".tsx": tree_sitter.Language(tree_sitter_typescript.language_tsx()),
            ".kt": tree_sitter.Language(tree_sitter_kotlin.language()),
            ".kts": tree_sitter.Language(tree_sitter_kotlin.language()),
        }
        
        self.nodes: Dict[str, CodeNode] = {}
        # Simple string-to-Node mapping to resolve call graph edges later
        self.symbol_map: Dict[str, str] = {}
        self.files_scanned: int = 0
        self.files_parsed: int = 0
        self.nodes_by_extension: Dict[str, int] = {}
        
    def _get_queries(self, ext: str) -> dict:
        """Return language-specific Tree-sitter queries for extraction."""
        if ext == ".py":
            return {
                "definitions": """
                    (function_definition name: (identifier) @name) @def
                    (class_definition name: (identifier) @name) @def
                """,
                "calls": """
                    (call function: (identifier) @call)
                    (call function: (attribute attribute: (identifier) @call))
                """
            }
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return {
                "definitions": """
                    (function_declaration name: (identifier) @name) @def
                    (method_definition name: (property_identifier) @name) @def
                    (method_signature name: (property_identifier) @name) @def
                    (lexical_declaration (variable_declarator name: (identifier) @name value: (arrow_function))) @def
                    (lexical_declaration (variable_declarator name: (identifier) @name value: (function))) @def
                    (assignment_expression left: (identifier) @name right: (arrow_function)) @def
                    (assignment_expression left: (identifier) @name right: (function)) @def
                    (class_declaration name: (identifier) @name) @def
                """,
                "calls": """
                    (call_expression function: (identifier) @call)
                    (call_expression function: (member_expression property: (property_identifier) @call))
                """
            }
        elif ext in [".kt", ".kts"]:
            return {
                "definitions": """
                    (function_declaration name: (identifier) @name) @def
                    (class_declaration name: (identifier) @name) @def
                """,
                "calls": """
                    (call_expression (identifier) @call)
                    (call_expression (navigation_expression . (identifier) @call))
                """
            }
        return {}

    def _is_within_class_like(self, node: tree_sitter.Node) -> bool:
        class_like_types = {
            "class_definition",
            "class_declaration",
            "object_declaration",
            "interface_declaration",
        }
        parent = node.parent
        while parent is not None:
            if parent.type in class_like_types:
                return True
            parent = parent.parent
        return False

    def _classify_definition_type(self, node: tree_sitter.Node) -> str:
        if node.type in {"class_definition", "class_declaration", "object_declaration", "interface_declaration"}:
            return "class"
        if node.type == "method_definition":
            return "method"
        if node.type in {"function_definition", "function_declaration"} and self._is_within_class_like(node):
            return "method"
        return "function"
        
    def parse_file(self, file_path: Path):
        self.files_scanned += 1
        ext = file_path.suffix
        if ext not in self.langs:
            return
            
        language = self.langs[ext]
        parser = tree_sitter.Parser(language)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            source_bytes = source_code.encode("utf8")
        except Exception as e:
            return # Skip unreadable files
            
        tree = parser.parse(source_bytes)
        queries = self._get_queries(ext)
        if not queries:
            return
        self.files_parsed += 1
            
        # Extract definitions
        try:
            def_query = tree_sitter.Query(language, queries['definitions'])
            qc = tree_sitter.QueryCursor(def_query)
            def_matches = qc.matches(tree.root_node)
        except Exception as e:
            print(f"Error compiling query for {file_path}: {e}")
            return
            
        for match in def_matches:
            # match is (pattern_index, capture_dict)
            capture_dict = match[1]
            def_nodes = capture_dict.get("def", [])
            name_nodes = capture_dict.get("name", [])
            
            if not def_nodes or not name_nodes:
                continue
                
            def_node = def_nodes[0]
            name_node = name_nodes[0]
            
            func_name = source_bytes[name_node.start_byte:name_node.end_byte].decode('utf8')
            
            # Now, extract all calls inside this function
            calls = []
            try:
                call_query = tree_sitter.Query(language, queries['calls'])
                c_qc = tree_sitter.QueryCursor(call_query)
                call_matches = c_qc.matches(def_node)
                
                for c_match in call_matches:
                    c_dict = c_match[1]
                    call_nodes = c_dict.get("call", [])
                    for c_node in call_nodes:
                        calls.append(source_bytes[c_node.start_byte:c_node.end_byte].decode('utf8'))
            except Exception:
                pass
            
            node_id = f"{file_path}:{def_node.start_byte}:{def_node.end_byte}:{func_name}"
            node_type = self._classify_definition_type(def_node)
            
            code_node = CodeNode(
                id=node_id,
                name=func_name,
                type=node_type,
                file_path=str(file_path),
                start_byte=def_node.start_byte,
                end_byte=def_node.end_byte,
                source=source_bytes[def_node.start_byte:def_node.end_byte].decode('utf8'),
                calls=list(set(calls))
            )
            
            from dataclasses import asdict
            self.nodes[node_id] = asdict(code_node)
            self.symbol_map.setdefault(func_name, node_id)
            self.nodes_by_extension[ext] = self.nodes_by_extension.get(ext, 0) + 1
            
    def build(self) -> Dict[str, Any]:
        """Walk the directory and parse all supported files."""
        ignored_dirs = {".git", "node_modules", ".venv"}
        for root, dirs, files in os.walk(self.target_dir, topdown=True):
            # Prune ignored directories early so walk still goes deep everywhere else.
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                # Always use the final extension so names like *.spec.ts are parsed.
                ext = Path(file).suffix
                if ext in self.langs:
                    self.parse_file(Path(root) / file)
                
        return self.nodes

if __name__ == "__main__":
    import sys
    idx = CodeAtlasIndexer("." if len(sys.argv) == 1 else sys.argv[1])
    nodes = idx.build()
    print(f"Indexed {len(nodes)} definitions.")
    for n in list(nodes.values())[:3]:
        print(f"[{n['type']}] {n['name']} (calls: {n['calls']})")
