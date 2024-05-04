import ast

def find_function_calls(node, calls=None):
    if calls is None:
        calls = []
    
    for child_node in ast.iter_child_nodes(node):
        find_function_calls(child_node, calls)

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            print(node, node.func.id)
            calls.append(node)
    return calls

def extract_function_calls(file_path, function_name):
    with open(file_path, 'r') as file:
        code = file.read()

    tree = ast.parse(code)
    calls = find_function_calls(tree, function_name)

    return calls

def get_called_functions(file_path):
    visited_functions = set()

    def recursive_traverse(node):
        print(node, node)
        if isinstance(node, ast.Module):
            for child_node in ast.iter_child_nodes(node):
                recursive_traverse(child_node)

        if isinstance(node, ast.FunctionDef):
            function_name = node.name
            if function_name not in visited_functions:
                visited_functions.add(function_name)
                print("Scanning function:", function_name)
                # find_function_calls(node, starting_function)
                for call_node in find_function_calls(node):
                    print(f"Found call to {call_node.func.id}")
                    recursive_traverse(call_node)

    with open(file_path, 'r') as file:
        code = file.read()

    tree = ast.parse(code)
    for node in ast.walk(tree):
        # print out node id
        val = node

        if isinstance(node, ast.Name):
            val = node.id
        if isinstance(node, ast.Call):
            val = node.func
        if isinstance(node, ast.FunctionDef):
            val = node.name
        if isinstance(node, ast.Expr):
            val = node.value
        if isinstance(node, ast.Assign):
            val = node.targets
        if isinstance(node, ast.Raise):
            val = node.exc
        if isinstance(node, ast.alias):
            val = node.name

        print ('Type:', type(node).__name__, 'Value: ', val)

        


        if isinstance(node, ast.FunctionDef):
            function_name = node.name
            if function_name not in visited_functions:
                visited_functions.add(function_name)
                print("Scanning function:", function_name)
                # find_function_calls(node, starting_function)
                # for call_node in find_function_calls(node):
                #     print(f"Found call to {call_node.func.id}")
                    # recursive_traverse(call_node)
        # if isinstance(node, ast.Module):
        #     for child_node in ast.iter_child_nodes(node):
        #         recursive_traverse(child_node)
    # recursive_traverse(tree)

# Example usage
if __name__ == '__main__':
    file_path = './code.py'
    get_called_functions(file_path)
