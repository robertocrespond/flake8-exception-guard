import ast
import builtins
import os
from importlib import util as importlib_util
import re
import sys
from types import ModuleType
from typing import Optional
import inspect
from copy import deepcopy
import textwrap
import warnings
import types
from collections import ChainMap

deprecated = lambda f: f

class ImportResolver:
    def __init__(self, file_path, _imports = None, _processed= None) -> None:
        self._imports = {} if _imports is None else _imports
        self._processed = set() if _processed is None else _processed
        self.file_path = file_path

        with open(file_path, 'r') as file:
            self.source_code = file.read()

        # TODO: this dedent might not be needed
        self.ast_tree = ast.parse(textwrap.dedent(self.source_code), filename=file_path)
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

    def __repr__(self) -> str:
        return f'Context({self.covered_exceptions}, {self.stack}, {self.fp})'


class FileScan:
    def __init__(self, fp: str):
        self.fp = fp
        self._ok = True

        with open(fp, 'r') as file:
            self.source_code = file.read()
        with open(fp, 'r') as file:
            self.source_code_lines = file.readlines()

        self.ast_tree = ast.parse(self.source_code, filename=fp)

        current_module_spec = importlib_util.spec_from_file_location('current_module', fp)
        self._current_module = importlib_util.module_from_spec(current_module_spec)
        current_module_spec.loader.exec_module(self._current_module)

        self._mem_addr_to_class_node = {}


    def _is_fcn(self, node, ctx):
        if ctx is None:
            return False
        
        return ctx and isinstance(ctx.node, ast.Call) and isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and not isinstance(ctx.prev.node, ast.Raise)

    def _is_method(self, node, ctx):
        if ctx is None:
            return False
        
        return ctx and isinstance(ctx.node, ast.Call) and isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load) and not isinstance(ctx.prev.node, ast.Raise)
        

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
        )
    
    def _process_fcn(self, func, _ids=None, _depth=0 , _ctx: Optional[Context] = None):
        if _ctx is not None:
            _ctx = self._deep_copy_ctx(_ctx)

        new_ctx = Context(
            prev=_ctx,
            node=None,
            covered_exceptions=_ctx.covered_exceptions if _ctx else {},
            stack=_ctx.stack if _ctx else [],
            fp=_ctx.fp if _ctx else self.fp,
        )




        sc_lines = self.source_code_lines

        try:
            vars = ChainMap(*inspect.getclosurevars(func)[:3])
            source = textwrap.dedent(inspect.getsource(func))
        # except Exception as e:
        #     raise e
        except (TypeError, OSError):
            exc = re.findall(r'\w+Error', func.__doc__)
            if exc:
                for exception_name in exc:
                    if exception_name not in new_ctx.covered_exceptions:
                        line_offset = open(new_ctx.fp, 'r').readlines().index(textwrap.dedent(source).split('\n')[0] + '\n')
                        debug_log = [f'        {s[0]} File: "{s[2]}", line {s[1]},' for s in new_ctx.stack] + [f'        {exception_name} File: "{new_ctx.fp}", line {line_offset + n.lineno}']
                        verbose_stack = '\n'.join(debug_log)
                        self._ok = False
                        print(f"{self.fp} {exception_name} not handled:\n{verbose_stack}")
            return
                #     if hasattr(builtins, e):
                #         yield getattr(builtins, e)
            # return

        # print(vars)
        # print(source)

        if inspect.isclass(func):
            fcn_file_path = inspect.getfile(func.__init__)
        else:
            fcn_file_path = inspect.getfile(func)
        new_ctx.fp = fcn_file_path
        upstream_cls = self

        # print(fcn_file_path)

        class _Visitor(ast.NodeTransformer):
            def __init__(self, log_id=""):
                self.nodes = []
                self.log_id = log_id
                self.order_op = 0

            def _order_op(self):
                self.order_op += 1
                return self.order_op

            def visit_Raise(self, n):
                self.nodes.append(n.exc)

            def visit_Call(self, n):
                c, ob = n.func, None
                if isinstance(c, ast.Attribute):
                    parts = []
                    while getattr(c, 'value', None):
                        parts.append(c.attr)
                        c = c.value
                    if c.id in vars:
                        ob = vars[c.id]
                        for name in reversed(parts):
                            try:
                                ob = getattr(ob, name)
                            except AttributeError:
                                exc = re.findall(r'\w+Error', ob.__doc__)
                                if exc:
                                    for exception_name in exc:
                                        if exception_name not in new_ctx.covered_exceptions:
                                            line_offset = open(new_ctx.fp, 'r').readlines().index(textwrap.dedent(source).split('\n')[0] + '\n')
                                            debug_log = [f'        {s[0]} File: "{s[2]}", line {s[1]},' for s in new_ctx.stack] + [f'        {exception_name} File: "{new_ctx.fp}", line {line_offset + n.lineno}']
                                            verbose_stack = '\n'.join(debug_log)
                                            upstream_cls._ok = False
                                            print(f"{upstream_cls.fp} {exception_name} not handled:\n{verbose_stack}")
                                
                

                elif isinstance(c, ast.Name):
                    if c.id in vars:
                        ob = vars[c.id]

                if ob is not None and id(ob) not in _ids:
                    line_offset = sc_lines.index(textwrap.dedent(source).split('\n')[0] + '\n')
                    new_ctx.stack = [s for s in new_ctx.stack] + [(ob.__name__, line_offset + n.lineno, new_ctx.fp)]
                    upstream_cls._process_fcn(ob, _ids=_ids, _depth=_depth+1, _ctx=new_ctx)
                    _ids.add(id(ob))

            def visit_Expr(self, n):
                if not isinstance(n.value, ast.Call):
                    return
                c, ob = n.value.func, None
                if isinstance(c, ast.Attribute):
                    parts = []
                    while getattr(c, 'value', None):
                        parts.append(c.attr)
                        c = c.value
                    if c.id in vars:
                        ob = vars[c.id]
                        for name in reversed(parts):
                            ob = getattr(ob, name)

                elif isinstance(c, ast.Name):
                    if c.id in vars:
                        ob = vars[c.id]

                if ob is not None and id(ob) not in _ids:
                    new_ctx.stack = [s for s in new_ctx.stack] + [(ob.__name__, n.lineno, new_ctx.fp)]
                    upstream_cls._process_fcn(ob, _ids=_ids, _depth=_depth+1, _ctx=new_ctx)
                    _ids.add(id(ob))

            def visit_Try(self, n):
                print(self._order_op(),'TRY', n.__dict__)
                for handler in n.handlers:
                    if isinstance(handler.type, ast.Tuple):
                        for _type in handler.type.elts:
                            new_ctx.covered_exceptions[_type.id] = new_ctx.covered_exceptions.get(_type.id, 0) + 1
                    else:
                        new_ctx.covered_exceptions[handler.type.id] = new_ctx.covered_exceptions.get(handler.type.id, 0) + 1
                print(new_ctx.covered_exceptions)
                self.generic_visit(n)

            def visit_ExceptHandler(self, n):
                # At this point have'nt explored the body of the except block (inner function calls)
                print(self._order_op(), 'EXC', n.__dict__)
                if isinstance(n.type, ast.Tuple):
                    for _type in n.type.elts:
                        new_ctx.covered_exceptions[_type.id] -= 1
                        if new_ctx.covered_exceptions[_type.id] == 0:
                            del new_ctx.covered_exceptions[_type.id]
                else:
                    new_ctx.covered_exceptions[n.type.id] -= 1
                    if new_ctx.covered_exceptions[n.type.id] == 0:
                        del new_ctx.covered_exceptions[n.type.id]
                print(new_ctx.covered_exceptions)
                self.generic_visit(n)

                

        print(func, new_ctx.covered_exceptions)
        v = _Visitor(log_id=func.__name__)
        v.visit(ast.parse(source))

        for n in v.nodes:
            if isinstance(n, (ast.Call, ast.Name)):
                exception_name = n.id if isinstance(n, ast.Name) else n.func.id

                # TODO: must check if the exception is a subclass of the caught exception
                # TODO: also here IOSError -> returns OSError, so get by key from somewhere else like builtins
                # if exc_name in vars:
                #     print(vars[exc_name])


                # exception_name = self._get_exception_name(n)

            # TODO: must check also with parent classes, i.e. if the exception is a subclass of the caught exception
            # print("     " * _depth, exception_name)

                if exception_name not in new_ctx.covered_exceptions:
                    line_offset = open(new_ctx.fp, 'r').readlines().index(textwrap.dedent(source).split('\n')[0] + '\n')
                    debug_log = [f'        {s[0]} File: "{s[2]}", line {s[1]},' for s in new_ctx.stack] + [f'        {exception_name} File: "{new_ctx.fp}", line {line_offset + n.lineno}']
                    verbose_stack = '\n'.join(debug_log)
                    self._ok = False
                    print(self._ok)
                    print(f"{self.fp} {exception_name} not handled:\n{verbose_stack}")



    def are_exceptions_caught(self, node) -> bool:
        self._process_fcn(node, ids=set())
        return self._ok
    
    def process_fcn(self, fcn) -> bool:
        self._process_fcn(fcn, _ids=set(), _depth=0, _ctx=None)
        print(self._ok)
        return self._ok


class Bubble:
    def __init__(self, base_path: str, entrypoint: str) -> None:
        self.base_path = base_path
        self.entrypoint = entrypoint
        self._exit_code = 0

    def _scan_file(self, file_path):
        file_scan = FileScan(fp=file_path)

        if not hasattr(file_scan._current_module, self.entrypoint):
            raise AttributeError(f"Entrypoint function not found: {self.entrypoint}")
        
        entrypoint_fcn = getattr(file_scan._current_module, self.entrypoint)
        return file_scan.process_fcn(entrypoint_fcn)

    def scan(self):
        if not os.path.exists(self.base_path):
            raise FileNotFoundError(f"File or directory not found: {self.base_path}")
    
        if os.path.isfile(self.base_path):
            ok = self._scan_file(self.base_path)
            if not ok:
                self._exit_code = 1
            return self._exit_code
        
        # directory
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    ok = self._scan_file(file_path)
                    if not ok:
                        self._exit_code = 1

        return self._exit_code
    

