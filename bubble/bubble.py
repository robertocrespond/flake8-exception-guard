import ast
import builtins
import os
from importlib import util as importlib_util
import re
from typing import Optional
import inspect
from copy import deepcopy
import textwrap
from collections import ChainMap


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

    def check_if_exception_is_uncovered(self, ctx, source, n, exception_name):
        if hasattr(builtins, exception_name):
            exc_cls = getattr(builtins, exception_name)
        else:
            spec = importlib_util.spec_from_file_location('current_module', ctx.fp)
            module = importlib_util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # get by key from somewhere else like builtins, maybe the current module
            exc_cls = getattr(module, exception_name, None)

        if exc_cls:
            # skip object base class
            anscestors = [anscestor.__name__ for anscestor in inspect.getmro(exc_cls)[:-1]]
        else:
            anscestors = [exception_name]

        exc_covered = False
        for anscestor in anscestors:
            if anscestor in ctx.covered_exceptions:
                exc_covered = True
                break

        if exc_covered is False:
            line_offset = open(ctx.fp, 'r').readlines().index(textwrap.dedent(source).split('\n')[0] + '\n')
            debug_log = [f'        {s[0]} File: "{s[2]}", line {s[1]},' for s in ctx.stack] + [f'        {exception_name} File: "{ctx.fp}", line {line_offset + n.lineno}']
            verbose_stack = '\n'.join(debug_log)
            self._ok = False
            print(f"{self.fp} {exception_name} not handled:\n{verbose_stack}")


        # print(exception_name, self._current_module.)

        # TODO: must check if the exception is a subclass of the caught exception
            # TODO: also here IOSError -> returns OSError, so get by key from somewhere else like builtins
            # if exc_name in vars:
            #     print(vars[exc_name])


            # exception_name = self._get_exception_name(n)

        # TODO: must check also with parent classes, i.e. if the exception is a subclass of the caught exception
        # print("     " * _depth, exception_name)
  

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

        try:
            vars = ChainMap(*inspect.getclosurevars(func)[:3])
            source = textwrap.dedent(inspect.getsource(func))
        except (TypeError, OSError):
            exc = re.findall(r'\w+Error', func.__doc__)
            for exception_name in exc:
                self.check_if_exception_is_uncovered(ctx=new_ctx, source=source, n=_ctx.node, exception=exception_name)
            return

        if inspect.isclass(func):
            fcn_file_path = inspect.getfile(func.__init__)
        else:
            fcn_file_path = inspect.getfile(func)
        new_ctx.fp = fcn_file_path
        upstream_cls = self

        class _Visitor(ast.NodeTransformer):
            def __init__(self, log_id=""):
                self.nodes = []
                self.log_id = log_id

            def visit_Raise(self, n):
                self.nodes.append(n.exc)

            def _handle_func_call(self, n, c):
                ob = None
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
                                for exception_name in exc:
                                    upstream_cls.check_if_exception_is_uncovered(ctx=new_ctx, source=source, n=n, exception_name=exception_name)

                elif isinstance(c, ast.Name):
                    if c.id in vars:
                        ob = vars[c.id]

                if ob is not None and id(ob) not in _ids:
                    line_offset = open(new_ctx.fp, 'r').readlines().index(textwrap.dedent(source).split('\n')[0] + '\n')
                    new_ctx.stack = [s for s in new_ctx.stack] + [(ob.__name__, line_offset + n.lineno, new_ctx.fp)]
                    new_ctx.node = n
                    upstream_cls._process_fcn(ob, _ids=_ids, _depth=_depth+1, _ctx=new_ctx)
                    _ids.add(id(ob))


            def visit_Call(self, n):
                self._handle_func_call(n, n.func)

            def visit_Expr(self, n):
                if not isinstance(n.value, ast.Call):
                    return
                self._handle_func_call(n, n.value.func)

            def visit_Try(self, n):
                for handler in n.handlers:
                    if isinstance(handler.type, ast.Tuple):
                        for _type in handler.type.elts:
                            new_ctx.covered_exceptions[_type.id] = new_ctx.covered_exceptions.get(_type.id, 0) + 1
                    else:
                        new_ctx.covered_exceptions[handler.type.id] = new_ctx.covered_exceptions.get(handler.type.id, 0) + 1
                self.generic_visit(n)

            def visit_ExceptHandler(self, n):
                if isinstance(n.type, ast.Tuple):
                    for _type in n.type.elts:
                        new_ctx.covered_exceptions[_type.id] -= 1
                        if new_ctx.covered_exceptions[_type.id] == 0:
                            del new_ctx.covered_exceptions[_type.id]
                else:
                    new_ctx.covered_exceptions[n.type.id] -= 1
                    if new_ctx.covered_exceptions[n.type.id] == 0:
                        del new_ctx.covered_exceptions[n.type.id]
                self.generic_visit(n)

        v = _Visitor(log_id=func.__name__)
        v.visit(ast.parse(source))

        for n in v.nodes:
            if isinstance(n, (ast.Call, ast.Name)):
                exception_name = n.id if isinstance(n, ast.Name) else n.func.id
                self.check_if_exception_is_uncovered(ctx=new_ctx, source=source, n=n, exception_name=exception_name)

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
    

