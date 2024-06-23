import builtins
from inspect import getclosurevars, getsource
from collections import ChainMap
import re
from textwrap import dedent
import ast, os
from other_code_2 import ultimate_test
import types
class MyException(Exception):
    pass

def sub3() -> int:
    if 102 > 101:
        raise AttributeError
    return 5 + sub4()

def sub4() -> int:
    raise ImportError
    return 5

def sub5() -> int:
    try:
        b = sub3()
    except ImportError:
        b = 3
    return  b

def unhandled():
    b = sub5()
    
    return 1 + b

def f2():
    x = g()

def g():
    # os.makedirs()
    raise Exception

class A():
    def method():
        g()
        raise IndentationError
import random
def f(x):
    try:
        x = f2()
    except MyException:
        x = 3
    # A.method()
    # s = random.choice()
    # os.makedirs()
    # g()
    # ultimate_test()
    # raise MyException
    # raise ValueError('argument')
    ...


def get_exceptions(func, ids=set()):
    try:
        vars = ChainMap(*getclosurevars(func)[:3])
        source = dedent(getsource(func))
    except TypeError:
        return
    except OSError:
        exc = re.findall(r'\w+Error', func.__doc__)
        if exc:
            for e in exc:
                if hasattr(builtins, e):
                    yield getattr(builtins, e)
        return

    class _visitor(ast.NodeTransformer):
        def __init__(self, log_id=""):
            self.nodes = []
            self.other = []
            self.log_id = log_id

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
                        ob = getattr(ob, name)

            elif isinstance(c, ast.Name):
                if c.id in vars:
                    ob = vars[c.id]

            if ob is not None and id(ob) not in ids:
                self.other.append(ob)
                ids.add(id(ob))

            print(f'[{self.log_id}: Call]', n.func.id, self.nodes, self.other)

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

            if ob is not None and id(ob) not in ids:
                self.other.append(ob)
                ids.add(id(ob))

    print(func)
    v = _visitor(log_id=func.__name__)
    node = ast.parse(source)
    v.visit(node)
    print(v.nodes, v.other)
    print()
    
    for n in v.nodes:
        if isinstance(n, (ast.Call, ast.Name)):
            name = n.id if isinstance(n, ast.Name) else n.func.id
            if name in vars:
                yield vars[name]

    for o in v.other:
        yield from get_exceptions(o)

# from tests.integration.cases.self_contained_module.single_exception import unhandled
# import random
# for e in get_exceptions(unhandled):
#     print(e)


print('\n\n------------------[SE]--------------\n\n')
from bubble.bubble import Bubble
x = Bubble(base_path=os.path.join(os.path.dirname(__file__), 'tests', 'integration', 'cases', 'same_file', 'same_file_multiple_exceptions_nested.py'), entrypoint='unhandled').scan()

# print(x)