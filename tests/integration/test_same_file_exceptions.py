
import warnings
from bubble import Bubble
from pathlib import Path
import os
import pytest
import re

CURRENT_FILE_PATH =  Path(__file__).parent.resolve()
REGEX_RAW_PATTERN = r'.*<Bubble>.*'
REGEX_PATTERN = re.compile(REGEX_RAW_PATTERN)

FILES = [
    'same_file_single_exception.py',
    'same_file_single_exception_nested.py',
    'same_file_multiple_exceptions.py',
    'same_file_multiple_exceptions_nested.py'
]

@pytest.mark.parametrize(('file_name',), [(file,) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_same_file_warning_throw_if_unhandled_exception(file_name):
    with pytest.warns(UserWarning, match=REGEX_RAW_PATTERN):
        Bubble(
            base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'same_file', file_name),
            entrypoint='unhandled'
        ).scan()


@pytest.mark.parametrize(('file_name',), [(file,) for file in FILES], ids=[f'file: {file}' for file in FILES])
def test_same_file_no_warning_if_handled_exception(file_name):
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        Bubble(
            base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'same_file', file_name),
            entrypoint='handled'
        ).scan()

        if any(REGEX_PATTERN.match(str(r.message)) for r in record if r.category == UserWarning):
            pytest.fail(f'Unexpected warning thrown: {record[0].message}')
