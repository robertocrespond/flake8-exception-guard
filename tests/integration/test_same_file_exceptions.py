
from bubble import Bubble
from pathlib import Path
import os
import pytest

CURRENT_FILE_PATH =  Path(__file__).parent.resolve()
FILES = [
    'same_file_single_exception.py',
    'same_file_single_exception_nested.py',
    'same_file_multiple_exceptions.py',
    'same_file_multiple_exceptions_nested.py'
]

@pytest.mark.parametrize(('file_name',), [(file,) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_same_file_warning_throw_if_unhandled_exception(file_name):
    exit_code = Bubble(
        base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'same_file', file_name),
        entrypoint='unhandled'
    ).scan()

    assert exit_code == 1


@pytest.mark.parametrize(('file_name',), [(file,) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_same_file_no_warning_if_handled_exception(file_name):
    exit_code = Bubble(
        base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'same_file', file_name),
        entrypoint='handled'
    ).scan()
    
    assert exit_code == 0


