import ast
import builtins
import inspect
import re
import sys
import textwrap
from collections import ChainMap
from copy import deepcopy
from dataclasses import dataclass
from importlib import util as importlib_util
from typing import Any
from typing import Generator
from typing import Optional
from typing import Tuple
from typing import Type

if sys.version_info >= (3, 8):
    import importlib.metadata as importlib_metadata
else:
    import importlib_metadata
import os


@dataclass
class Context:
    prev: "Context"
    node: ast.AST
    covered_exceptions: dict = None
    stack: list = None
    fp: str = None

    def __repr__(self) -> str:
        return f"Context({self.covered_exceptions}, {self.stack}, {self.fp})"


class FileScan:
    def __init__(self, fp: str):
        self.fp = fp
        self._ok = True

        with open(fp, "r") as file:
            self.source_code = file.read()
        with open(fp, "r") as file:
            self.source_code_lines = file.readlines()

        self.ast_tree = ast.parse(self.source_code, filename=fp)

        current_module_spec = importlib_util.spec_from_file_location(
            "current_module", fp
        )
        self._current_module = importlib_util.module_from_spec(
            current_module_spec
        )
        try:
            current_module_spec.loader.exec_module(self._current_module)
        except Exception:
            self._ok = False

        self.errors = set()

    def check_if_exception_is_uncovered(self, ctx, source, n, exception_name):
        if hasattr(builtins, exception_name):
            exc_cls = getattr(builtins, exception_name)
        else:
            try:
                spec = importlib_util.spec_from_file_location(
                    "current_module", ctx.fp
                )
                module = importlib_util.module_from_spec(spec)
                spec.loader.exec_module(module)
                # get by key from somewhere else like builtins, maybe the current module
                exc_cls = getattr(module, exception_name, None)
            except Exception:
                return

        if exc_cls:
            # skip object base class
            anscestors = [
                anscestor.__name__
                for anscestor in inspect.getmro(exc_cls)[:-1]
            ]
        else:
            anscestors = [exception_name]

        # FIXME: handles exceptions such as IOError that its class is OSError, so if IOError is explicitely caught,
        # it should be included in the anscestors
        if exception_name not in anscestors:
            anscestors.insert(0, exception_name)

        exc_covered = False
        for anscestor in anscestors:
            if anscestor in ctx.covered_exceptions:
                exc_covered = True
                break

        if exc_covered is False:
            line_offset = 0
            for i, line in enumerate(open(ctx.fp, "r").readlines()):
                if textwrap.dedent(source).split("\n")[0] in line:
                    line_offset = i
                    break

            # line_offset = open(ctx.fp, 'r').readlines().index(textwrap.dedent(source).split('\n')[0] + '\n')
            debug_log = [
                f'        {s[0]} File: "{s[3]}", line {s[1]},'
                for s in ctx.stack
            ] + [
                f'        {exception_name} File: "{ctx.fp}", line {line_offset + n.lineno}'
            ]
            lines = [(s[1], s[2]) for s in ctx.stack] + [
                (line_offset + n.lineno, n.col_offset)
            ]
            verbose_stack = "\n".join(debug_log)
            self._ok = False
            # print(f"{self.fp} {exception_name} not handled:\n{verbose_stack}")
            # self.errors.add((line_offset + n.lineno, n.col_offset, f"{exception_name} not handled:\n{verbose_stack}"))
            # Give first line/col as its not where the exception is raised, but where code could/should be addressed
            self.errors.add(
                (
                    lines[0][0],
                    lines[0][1],
                    f"{exception_name} not handled\n{verbose_stack}",
                )
            )

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
            prev=self._deep_copy_ctx(ctx.prev),  # TODO: might not be needed
            node=ctx.node,
            covered_exceptions=deepcopy(ctx.covered_exceptions),
            stack=deepcopy(ctx.stack),
            fp=deepcopy(ctx.fp),
        )

    def _process_fcn(
        self, func, _ids=None, _depth=0, _ctx: Optional[Context] = None
    ):
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
            if func.__doc__ is None:
                return

            exc = [
                e
                for e in re.findall(r"\w+Error", func.__doc__)
                if hasattr(builtins, e)
            ]

            for exception_name in exc:
                self.check_if_exception_is_uncovered(
                    ctx=new_ctx,
                    source="",
                    n=_ctx.node,
                    exception_name=exception_name,
                )
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
                    while getattr(c, "value", None) and hasattr(c, "attr"):
                        parts.append(c.attr)
                        c = c.value

                    if hasattr(c, "id") and c.id in vars:
                        ob = vars[c.id]
                        for name in reversed(parts):
                            try:
                                ob = getattr(ob, name)
                            except AttributeError:
                                exc = [
                                    e
                                    for e in re.findall(
                                        r"\w+Error", ob.__doc__
                                    )
                                    if hasattr(builtins, e)
                                ]
                                for exception_name in exc:
                                    upstream_cls.check_if_exception_is_uncovered(
                                        ctx=new_ctx,
                                        source=source,
                                        n=n,
                                        exception_name=exception_name,
                                    )

                elif isinstance(c, ast.Name):
                    if c.id in vars:
                        ob = vars[c.id]

                if ob is not None and id(ob) not in _ids:
                    line_offset = 0
                    for i, line in enumerate(
                        open(new_ctx.fp, "r").readlines()
                    ):
                        if textwrap.dedent(source).split("\n")[0] in line:
                            line_offset = i
                            break
                    fwd_ctx = upstream_cls._deep_copy_ctx(new_ctx)
                    fwd_ctx.stack = [s for s in fwd_ctx.stack] + [
                        (
                            ob.__name__,
                            line_offset + n.lineno,
                            n.col_offset,
                            new_ctx.fp,
                        )
                    ]
                    fwd_ctx.node = n
                    _ids.add(id(ob))
                    upstream_cls._process_fcn(
                        ob, _ids=_ids, _depth=_depth + 1, _ctx=fwd_ctx
                    )

            def visit_Call(self, n):
                self._handle_func_call(n, n.func)

            def visit_Expr(self, n):
                if not isinstance(n.value, ast.Call):
                    return
                self._handle_func_call(n, n.value.func)

            def visit_Try(self, n):
                for handler in n.handlers:
                    if handler.type is None:
                        continue
                    if hasattr(handler.type, "elts"):
                        for _type in handler.type.elts:
                            new_ctx.covered_exceptions[_type.id] = (
                                new_ctx.covered_exceptions.get(_type.id, 0) + 1
                            )
                    else:
                        new_ctx.covered_exceptions[handler.type.id] = (
                            new_ctx.covered_exceptions.get(handler.type.id, 0)
                            + 1
                        )
                self.generic_visit(n)

            def visit_ExceptHandler(self, n):
                if n.type is None:
                    return self.generic_visit(n)
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
                if (
                    isinstance(n, ast.Name)
                    and hasattr(n, "id")
                    or hasattr(n.func, "id")
                ):
                    exception_name = (
                        n.id if isinstance(n, ast.Name) else n.func.id
                    )
                    self.check_if_exception_is_uncovered(
                        ctx=new_ctx,
                        source=source,
                        n=n,
                        exception_name=exception_name,
                    )

    def are_exceptions_caught(self, node) -> bool:
        self._process_fcn(node, ids=set())
        return self._ok

    def process_fcn(self, fcn) -> bool:
        self.errors = set()
        self._process_fcn(fcn, _ids=set(), _depth=0, _ctx=None)
        return self._ok

    def clear_errors(self):
        self.errors = set()


class Plugin:
    name = __name__
    version = importlib_metadata.version(__name__)

    def __init__(self, filename, lines, tree: ast.AST) -> None:
        self._tree = tree
        self.filename = filename
        self.fscan = FileScan(os.path.abspath(self.filename))
        self.succesful_module_import = self.fscan._ok
        self.lines = lines

    def run(self) -> Generator[Tuple[int, int, str, Type[Any]], None, None]:
        # Executed for every file, hence why its a generator
        if not self.succesful_module_import:
            return

        for node in ast.walk(self._tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in self.fscan._current_module.__dict__:
                    self.fscan.process_fcn(
                        self.fscan._current_module.__dict__[node.name]
                    )
                for error in self.fscan.errors:
                    yield (
                        error[0],
                        error[1],
                        f"FEG001 [{node.name}] {error[2]}",
                        type(self),
                    )
                self.fscan.clear_errors()

            elif isinstance(node, ast.ClassDef):
                if node.name not in self.fscan._current_module.__dict__:
                    return

                cls = self.fscan._current_module.__dict__[node.name]

                for function_def in node.body:
                    if isinstance(function_def, ast.FunctionDef):
                        if function_def.name in cls.__dict__:
                            self.fscan.process_fcn(
                                cls.__dict__[function_def.name]
                            )
                        for error in self.fscan.errors:
                            yield (
                                error[0],
                                error[1],
                                f"FEG001 [{function_def.name}] {error[2]}",
                                type(self),
                            )
                        self.fscan.clear_errors()
