import ast
import inspect
from pathlib import Path
import os
import pytest
from flake8_exception_guard import Plugin
from typing import Set
from importlib import util as importlib_util


def _results(fp: str, fcn_name: str) -> Set[str]:
    # load module
    current_module_spec = importlib_util.spec_from_file_location('current_module', fp)
    module = importlib_util.module_from_spec(current_module_spec)
    current_module_spec.loader.exec_module(module)

    fcn = getattr(module, fcn_name)
    source_code = inspect.getsource(fcn)
    ast_tree = ast.parse(source_code)

    return [x for x in Plugin(fp, lines=open(fp, 'r').readlines(), tree=ast_tree).run()]


CURRENT_FILE_PATH =  Path(__file__).parent.resolve()
FILES = [
    ('single_exception.py', {'IOError':1}),
    ('single_exception_nested.py', {'IOError': 1}),
    ('multiple_exceptions.py', {'AttributeError': 1, 'IOError': 1}),
    ('multiple_exceptions_nested.py', {'AttributeError': 1, 'IOError': 1}),
]

@pytest.mark.parametrize(('file_name', 'exceptions',), FILES, ids=[f'file: {file[0]}' for file in FILES])
def test_self_contained_module_warning_throw_if_unhandled_exception(file_name, exceptions):
    fp = os.path.join(CURRENT_FILE_PATH, 'cases', 'self_contained_module', file_name)
    res = _results(fp, 'unhandled')

    assert len(res) == sum(exceptions.values())
    for e in res:
        assert e[2].split(" ")[2] in exceptions.keys()
        exceptions[e[2].split(" ")[2]] -= 1
    assert all([v == 0 for v in exceptions.values()])


@pytest.mark.parametrize(('file_name',), [(file[0],) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_self_contained_module_no_warning_if_handled_exception(file_name):
    fp = os.path.join(CURRENT_FILE_PATH, 'cases', 'self_contained_module', file_name)
    res = _results(fp, 'handled')

    assert len(res) == 0