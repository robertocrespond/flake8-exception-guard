import ast

class FunctionBVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'b':
            print(node)
            # Jump to file_b.py and process function b
            with open(self.filename, 'r') as f:
                file_b_content = f.read()

            file_b_ast = ast.parse(file_b_content)
            print(file_b_ast)

            
            self.generic_visit(file_b_ast)
        else:
            self.generic_visit(node)

    # You can override other visit methods to handle different AST nodes as needed

def main():
    filename_a = 'file_a.py'
    with open(filename_a, 'r') as f:
        file_a_content = f.read()

    file_a_ast = ast.parse(file_a_content)
    visitor = FunctionBVisitor('file_b.py')
    x = visitor.visit(file_a_ast)
    # print(x)

if __name__ == "__main__":
    main()
