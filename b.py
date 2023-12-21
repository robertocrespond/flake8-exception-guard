import ast
from importlib import util as importlib_util
import os

class ExceptionChecker(ast.NodeVisitor):
    def __init__(self):
        self.exceptions_raised = set()
        self.exceptions_caught = set()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'sub':
            self.exceptions_raised.update(self.get_exceptions(node))

    def visit_Try(self, node):
        for handler in node.handlers:
            if isinstance(handler.type, ast.Name):
                exception_name = handler.type.id
                self.exceptions_caught.add(exception_name)

    def get_exceptions(self, node):
        exceptions = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Raise):
                if item.exc:
                    if isinstance(item.exc, ast.Name):
                        exceptions.add(item.exc.id)

        return exceptions

def analyze_file(file_path, base_path):
    with open(file_path, 'r') as file:
        source_code = file.read()

    ast_tree = ast.parse(source_code, filename=file_path)

    import_nodes = [node for node in ast.walk(ast_tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]

    sub_spec = importlib_util.find_spec("other_code")
    print('SPEC ', sub_spec)

    sub_module = importlib_util.module_from_spec(sub_spec)
    sub_spec.loader.exec_module(sub_module)
    sub_file_path = os.path.abspath(sub_spec.origin)
    print(sub_file_path)
    
    # for import_node in import_nodes:
    #     for alias in import_node.names:
    #         sub_module_name = importlib_util.resolve_name(alias.name, base_path)
    #         import_id = f"{import_node.module}.{sub_module_name}" if hasattr(import_node, "module") else sub_module_name
    #         sub_spec = importlib_util.find_spec(import_id)
    #         print(alias.name, base_path, import_id, sub_spec)
    
    
    print(import_nodes)
    checker = ExceptionChecker()
    checker.visit(ast_tree)

    return checker.exceptions_raised, checker.exceptions_caught

def main():
    file_path = 'code.py'
    base_path = '/Users/rcrespo/Downloads/playground/error'
    exceptions_raised, exceptions_caught = analyze_file(file_path, base_path)

    print(f"Exceptions raised by 'sub': {exceptions_raised}")
    print(f"Exceptions caught in try-except blocks: {exceptions_caught}")

    for exception in exceptions_raised:
        if exception not in exceptions_caught:
            print(f"ALERT: Exception '{exception}' raised by 'sub' is not caught in a try-except block.")

if __name__ == "__main__":
    main()