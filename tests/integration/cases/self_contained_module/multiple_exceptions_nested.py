# append current dir to path
import sys
from pathlib import Path
current_dir = Path(__file__).parent.resolve()
sys.path.append(str(current_dir))

from example.other_b import raises_io_error_and_attribute_error_indirectly
import pytest


# *********************************************************************************
### Entrypoints

def handled():
    try:
        b = raises_io_error_and_attribute_error_indirectly()
    except (IOError, AttributeError):
        b = 2


    # check if multiple exceptions are handled at once
    try:
        b = raises_io_error_and_attribute_error_indirectly()
    except (IOError, AttributeError):
        b = 2
    
    # check if multiple exceptions are handled separately
    try:
        try:
            b = raises_io_error_and_attribute_error_indirectly()
        except AttributeError:
            b = 2
    except IOError:
        b = 3

    return 1 + b

def unhandled():
    b = raises_io_error_and_attribute_error_indirectly()
    
    return 1 + b

def returns_1():
    return 1

class Ajask:
    # test defining something here
    def __init__(self):
        self.a = 1
    
    def t2(self, a: int = 1):
        try:
            asd = raises_io_error_and_attribute_error_indirectly()
        except (AttributeError):
            ...

        return a




def t1():
    y = returns_1()
    x = Ajask()
    a = x.t2(100)
    return a + y

# # import inspect
# # s = inspect.getsource(ABC)
# # # s = inspect.getsourcefile(ABC)
# # # s = inspect.getfile(ABC)
# s = Ajask()

# print(id(s))
# print(hex(id(s)))
# print(s)