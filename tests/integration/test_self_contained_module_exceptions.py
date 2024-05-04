
from bubble import Bubble
from pathlib import Path
import os
import pytest

CURRENT_FILE_PATH =  Path(__file__).parent.resolve()
FILES = [
    'single_exception.py',
    'single_exception_nested.py',
    'multiple_exceptions.py',
    'multiple_exceptions_nested.py',
]

@pytest.mark.parametrize(('file_name',), [(file,) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_self_contained_module_warning_throw_if_unhandled_exception(file_name):
    exit_code = Bubble(
        base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'self_contained_module', file_name),
        entrypoint='unhandled'
    ).scan()

    assert exit_code == 1


@pytest.mark.parametrize(('file_name',), [(file,) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_self_contained_module_no_warning_if_handled_exception(file_name):
    exit_code = Bubble(
        base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'self_contained_module', file_name),
        entrypoint='handled'
    ).scan()
    
    assert exit_code == 0

