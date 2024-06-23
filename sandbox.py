import ast

source_code = """
def sub5() -> int:
    try:
        b = sub3()
    except ImportError:
        b = 3
    return b
"""

import textwrap
# Parse the source code into an AST
tree = ast.parse(textwrap.dedent(source_code))

# Define a function to recursively print all nodes
def print_ast_nodes(node, indent=0):
    print(' ' * indent + str(type(node)), ast.dump(node, annotate_fields=True))
    for child in ast.iter_child_nodes(node):
        print_ast_nodes(child, indent + 4)

# Print all nodes in the AST
print_ast_nodes(tree)