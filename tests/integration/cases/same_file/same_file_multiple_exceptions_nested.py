
def sub() -> int:
    x = 5
    return x + sub2()

def sub2() -> int:
    return 5 + sub3()

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


# *********************************************************************************
### Entrypoints
def handled():
    # check if multiple exceptions are handled at once
    try:
        b = sub()
    except (AttributeError, ImportError):
        b = 2
    
    # check if multiple exceptions are handled separately
    try:
        try:
            b = sub()
        except AttributeError:
            b = 2
    except ImportError:
        b = 3

    # check if multiple exceptions are handled separately, within nested calls
    try:
        b = sub5()
    except AttributeError:
        b = 3

    
    return 1 + b

def unhandled():
    b = sub5()
    
    return 1 + b
