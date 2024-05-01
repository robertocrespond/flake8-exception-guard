# append current dir to path
import sys
from pathlib import Path
current_dir = Path(__file__).parent.resolve()
sys.path.append(str(current_dir))

from example.other_b import raises_io_error_indirectly



# *********************************************************************************
### Entrypoints

def handled():
    try:
        b = raises_io_error_indirectly()
    except IOError:
        b = 2

    return 1 + b

def unhandled():
    b = raises_io_error_indirectly()
    
    return 1 + b
