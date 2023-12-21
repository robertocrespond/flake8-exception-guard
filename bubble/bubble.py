import ast
import os
from importlib import util as importlib_util
import sys
from types import ModuleType
from typing import Optional
import inspect
from copy import deepcopy

class ImportResolver:
    def __init__(self, file_path, _imports = None, _processed= None) -> None:
        self._imports = {} if _imports is None else _imports
        self._processed = set() if _processed is None else _processed
        self.file_path = file_path

        with open(file_path, 'r') as file:
            self.source_code = file.read()

        self.ast_tree = ast.parse(self.source_code, filename=file_path)
        self._parse_imports()

    def _is_installed(self, module_id):
        if module_id in sys.modules:
            return True
        
        sub_spec = importlib_util.find_spec(module_id)

        # TODO: I don't think this holds for all installations
        return sub_spec.origin == 'built-in' or sub_spec.origin == 'frozen' or sub_spec.origin.startswith('/Library/Frameworks/')

    def _get_import_path(self, spec):
        ...

    def _parse_imports(self):
        import_nodes = [node for node in ast.walk(self.ast_tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]

        # TODO: this should be done only to top level imports and then process the imports that are declared on functions upon scanning a functionDeF


        for import_node in import_nodes:
            if isinstance(import_node, ast.Import):
                module_id = import_node.names[0].name

            if isinstance(import_node, ast.ImportFrom):
                module_id = import_node.module


            if module_id is None or module_id in self._processed:
                continue

            if self._is_installed(module_id):
                print(f'{module_id} is an installed module. Not scanning. Skipping. Make sure to check if there could by errors.')
                self._processed.add(module_id)
                continue

            sub_spec = importlib_util.find_spec(module_id)

            sub_module = importlib_util.module_from_spec(sub_spec)
            # sub_spec.loader.exec_module(sub_module)

            if sub_spec.origin == 'built-in':
                print(f'{module_id} is built-in. Not scanning. Skipping. Make sure to check if there could by errors.')
                continue
            if sub_spec.origin == 'frozen':
                print(f'{module_id} is frozen. Not scanning. Skipping. Make sure to check if there could by errors.')
                continue
            
            sub_file_path = os.path.abspath(sub_spec.origin)
            if sub_file_path.endswith('.py'):
                self._imports[module_id] = ImportResolver(sub_file_path, self._imports, self._processed)
                print(self.file_path, module_id, sub_file_path, self._imports)


from dataclasses import dataclass

@dataclass
class Context:
    prev: "Context"
    node: ast.AST
    covered_exceptions: dict = None
    stack: list = None
    fp: str = None
    module: ModuleType = None


class FileScan:
    def __init__(self, fp: str):
        self.fp = fp

        with open(fp, 'r') as file:
            self.source_code = file.read()

        self.ast_tree = ast.parse(self.source_code, filename=fp)

        current_module_spec = importlib_util.spec_from_file_location('current_module', fp)
        self._current_module = importlib_util.module_from_spec(current_module_spec)
        current_module_spec.loader.exec_module(self._current_module)


    def _get_exception_name(self, node):
        if isinstance(node.exc, ast.Attribute):
            return f"{node.exc.value.id}.{node.exc.attr}"
        elif isinstance(node.exc, ast.Name):
            return node.exc.id
        elif isinstance(node.exc, ast.Call):
            return node.exc.func.id
        return None
    
    def _deep_copy_ctx(self, ctx):
        if ctx is None:
            return None
        return Context(
            prev=self._deep_copy_ctx(ctx.prev), # TODO: might not be needed
            node=ctx.node,
            covered_exceptions=deepcopy(ctx.covered_exceptions),
            stack=deepcopy(ctx.stack),
            fp=deepcopy(ctx.fp),
            module=ctx.module
        )

    def _process_fcn(self, node, _depth=0 , _ctx: Optional[Context] = None):
        if _ctx is not None:
            _ctx = self._deep_copy_ctx(_ctx)

        new_ctx = Context(
            prev=_ctx,
            node=node,
            covered_exceptions=_ctx.covered_exceptions if _ctx else {},
            stack=_ctx.stack if _ctx else [],
            fp=_ctx.fp if _ctx else self.fp,
            module=_ctx.module if _ctx else self._current_module
        )

        #### DEBUG
        # print("     " * _depth, node, _ctx)
        # if isinstance(node, ast.Name):
        #     print("     " * _depth, node.id)


        if isinstance(node, ast.Try):
            for handler in node.handlers:
                if isinstance(handler.type, ast.Tuple):
                    for _type in handler.type.elts:
                        new_ctx.covered_exceptions[_type.id] = new_ctx.covered_exceptions.get(_type.id, 0) + 1
                else:
                    new_ctx.covered_exceptions[handler.type.id] = new_ctx.covered_exceptions.get(handler.type.id, 0) + 1
        
        if isinstance(node, ast.ExceptHandler):
            if isinstance(node.type, ast.Tuple):
                for _type in node.type.elts:
                    new_ctx.covered_exceptions[_type.id] -= 1
                    if new_ctx.covered_exceptions[_type.id] == 0:
                        del new_ctx.covered_exceptions[_type.id]
            else:
                new_ctx.covered_exceptions[node.type.id] -= 1
                if new_ctx.covered_exceptions[node.type.id] == 0:
                    del new_ctx.covered_exceptions[node.type.id]

        if isinstance(node, ast.Raise):
            exception_name = self._get_exception_name(node)

            # TODO: must check also with parent classes, i.e. if the exception is a subclass of the caught exception
            # print("     " * _depth, exception_name)
            debug_log = [f'        {s[0]} File: "{s[2]}", line {s[1]},' for s in new_ctx.stack] + [f'        {exception_name} File: "{_ctx.fp}", line {node.lineno}']

            if exception_name not in new_ctx.covered_exceptions:
                verbose_stack = '\n'.join(debug_log)
                print(f"{self.fp} {exception_name} not caught:\n{verbose_stack}")

            # TODO: must decrease the count of the exception in the context

        # Function Call
        if _ctx and isinstance(_ctx.node, ast.Call) and isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and not isinstance(_ctx.prev.node, ast.Raise):
            fcn_name = node.id
            new_ctx.stack = [s for s in new_ctx.stack] + [(fcn_name, node.lineno, _ctx.fp)]

            # load it

            # TODO: I have to enter the function recursively.
            # Have to go to fcn sub, then check if it is calling any functions.
            # Need to do DFS, forwarding context of all caught exceptions and then start checking if the function is raising any of the exceptions that are caught in the context.
            # print("     " * _depth, fcn_name, hasattr(self._current_module, fcn_name))
            if not hasattr(_ctx.module, fcn_name):

                if __builtins__.get(fcn_name):
                    print(f"Function `{fcn_name}` is builtin so ignoring")
                    return


                # if inspect.getmodule(p).__name__ == "builtins":
                #     print(f"Function {fcn_name} is builtin so ignoring")
                #     return

                # if inspect.getmodule(print)
                # TODO: inner function that is not exposed to module
                # print(_ctx.module)
                # print(inspect.getmodule(print).__name__ == "bultins")
                print(f"Function {fcn_name} not found in {_ctx.fp}")
                return

            fcn = getattr(_ctx.module, fcn_name)
            fcn_file_path = inspect.getfile(fcn)

            if fcn_file_path == self.fp:
                for _n in ast.walk(ast.parse(self.source_code)):
                    if isinstance(_n, ast.FunctionDef) and _n.name == fcn_name:
                        self._process_fcn(_n, _depth+1, new_ctx)
            else:
                fcn_module = inspect.getmodule(fcn)

                nested_new_ctx = self._deep_copy_ctx(new_ctx)
                nested_new_ctx.fp = fcn_file_path
                nested_new_ctx.module = fcn_module
                fcn_file_ast = ast.parse(open(fcn_file_path, 'r').read(), filename=fcn_file_path)

                # fcn_source = inspect.getsource(fcn)

                for _n in ast.walk(fcn_file_ast):
                    if isinstance(_n, ast.FunctionDef) and _n.name == fcn_name:
                        self._process_fcn(_n, _depth+1, nested_new_ctx)
                



                # print("     " * _depth, fcn_name, fcn_module, fcn_file)
                # fcn_ast = ast.parse(fcn_source, filename=inspect.getfile(fcn))

                # get function module and get ast tree from module
                # print(fcn.__module__)
                # 



                # new_ast = [node for node in ast.walk(ast.parse(self.source_code)) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom) or (isinstance(node, ast.FunctionDef) and node.name == fcn_name)]
                # new_ast = ast.parse(ast.unparse(new_ast))
                # TODO: should just be imports before code, this can be build on the outer iteration
                # import_nodes = [node for node in ast.walk(self.ast_tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]
                # fcn_source = ast.unparse(import_nodes) + '\n\n\n' + fcn_source
                # fcn_ast = ast.parse(fcn_source)
                


                # fcn_ast = import_nodes + [node for node in ast.walk(fcn_ast)]
                
                # print('\n\n\n ',ast.unparse(import_nodes), '\n\n\n')


            # source_code = self._get_function_source_code(fcn_name)


            # TODO: find the source code for the function
            #    - check if the function is defined in the current module
            #    - check if the function is imported

            # TODO: load the module
            # TODO: ast parse module
            # TODO: get function


            # TODO: check if the function is defined in the current module

            # TODO: check if the function can raise an exception

            # TODO: check if call is covered by a try/except block










        for child_node in ast.iter_child_nodes(node):
            self._process_fcn(child_node, _depth+1, new_ctx)




            # if hasattr(child_node, "body"):
            #     for item in node.body:

    def scan_function(self, node):
        return self._process_fcn(node)






class Bubble:
    def __init__(self, base_path) -> None:
        self.base_path = base_path

    def _has_inspect_decorator(self, node):
        return any(
            isinstance(decorator, ast.Name) and decorator.id == "entrypoint"
            for decorator in node.decorator_list
        )

    def _scan_file(self, file_path):
        file_scan = FileScan(fp=file_path)

        for node in ast.walk(file_scan.ast_tree):
            if isinstance(node, ast.FunctionDef) and self._has_inspect_decorator(node):
                file_scan.scan_function(node)
        
    def scan(self):
        if os.path.isfile(self.base_path):
            return self._scan_file(self.base_path)

        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self._scan_file(file_path)


