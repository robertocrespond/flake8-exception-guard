import ast

def analyze_imports(code):
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            print("Absolute Import:")
            for alias in node.names:
                print(f" - {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            print("Relative/Absolute Import:")
            print(f" - From: {node.module}")
            if node.level > 0:
                print(f"   - Relative Import with {node.level} dots")
            for alias in node.names:
                print(f"   - {alias.name}")

# Example code
code = """
import module1
from module2 import function1
from ..module3 import function2
"""

analyze_imports(code)