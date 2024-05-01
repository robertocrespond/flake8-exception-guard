
from bubble import Bubble
from pathlib import Path
import os
import pytest

CURRENT_FILE_PATH =  Path(__file__).parent.resolve() 

def test_error_if_file_not_found():
    # test throws FileNotFoundError if file not found
    with pytest.raises(FileNotFoundError):
        Bubble(
            base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'same_file', 'FILE_THAT_DOES_NOT_EXIST'),
            entrypoint='main'
        ).scan()


def test_error_if_entrypoint_not_found():
    # test throws AttributeError if entrypoint not found
    with pytest.raises(AttributeError):
        Bubble(
            base_path=os.path.join(CURRENT_FILE_PATH, 'cases', 'same_file', 'same_file_single_exception.py'),
            entrypoint='abcsksd'
        ).scan()
