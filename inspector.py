import ast
import inspect
from collections import defaultdict
import random

class Inspector:
    def __init__(self):
        self.exceptions_by_module = defaultdict(list)

    def inspect_function(self, func):
        source = inspect.getsource(func)
        print(source)
        # module_name = func.__module__
        tree = ast.parse(source)
        result = []



        return result
    
    def _process_function(self, node, result):
        if hasattr(node, "body"):
            for item in node.body:
                self._process_function(item, result)

    
        
        if (isinstance(node, ast.Expr) or isinstance(node, ast.Assign)) and isinstance(node.value, ast.Call):
            fcn_name = node.value.func.id

            # find the source code for the function
            # func = self._get_function_by_name(fcn_name)
            # if func:
            #     self.inspect_function(func)
            #     print(func)
            #     print("Found function")




        if isinstance(node, ast.Raise):
            exception_name = self._get_exception_name(node)
            if exception_name:
                result.append(exception_name)

    def _has_inspect_decorator(self, node):
        return any(
            isinstance(decorator, ast.Name) and decorator.id == "safe"
            for decorator in node.decorator_list
        )

    def _get_exception_name(self, node):
        if isinstance(node.exc, ast.Attribute):
            return f"{node.exc.value.id}.{node.exc.attr}"
        elif isinstance(node.exc, ast.Name):
            return node.exc.id
        elif isinstance(node.exc, ast.Call):
            return node.exc.func.id
        return None
    

    def inspect_file(self, source_code: str):
        tree = ast.parse(source_code)
        result= []
        for item in tree.body:
            if isinstance(item, ast.FunctionDef) and self._has_inspect_decorator(item):
                self._process_function(item, result)



if __name__ == "__main__":
    inspector = Inspector()

    FILE_NAME = "code.py"

    with open(FILE_NAME, 'r') as f:
        source_code = f.read()

    inspector.inspect_file(source_code)
