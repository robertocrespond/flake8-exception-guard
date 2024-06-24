import random

from random import random

def sub() -> int:
    aaa = .5

    s = random()
    print(random.__doc__)

    if random.random() < aaa:
        raise IOError
    
    return 10


# *********************************************************************************
### Entrypoints

def handled():
    try:
        b = sub()
    except IOError:
        b = 2

    
    return 1 + b

def unhandled():
    b = sub()
    
    return 1 + b

class A():
    def xyz():
        raise IndentationError
