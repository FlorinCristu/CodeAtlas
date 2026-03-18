import tree_sitter
import tree_sitter_python

lang = tree_sitter.Language(tree_sitter_python.language())
parser = tree_sitter.Parser(lang)

src = b"def hello_world():\n    print('hello')\n"
tree = parser.parse(src)

query = tree_sitter.Query(lang, "(function_definition name: (identifier) @name) @def")
qc = tree_sitter.QueryCursor(query)
captures = qc.captures(tree.root_node)

print(type(captures))
for c in captures:
    print(c)






