import random

def sub() -> int:
    aaa = .5

    if random.random() < aaa:
        raise Exception
    
    return 10

def sub2() -> int:
    return 10