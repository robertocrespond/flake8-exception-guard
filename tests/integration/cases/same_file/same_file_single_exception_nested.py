
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
    return 5


# *********************************************************************************
### Entrypoints
def handled():
    try:
        b = sub()
    except AttributeError:
        b = 2
    
    return 1 + b

def unhandled():
    b = sub()
    
    return 1 + b
