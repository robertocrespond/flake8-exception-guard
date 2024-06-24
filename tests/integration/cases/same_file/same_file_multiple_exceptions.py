import random


def sub() -> int:
    aaa = 0.5

    if random.random() < aaa:
        raise IOError

    raise AttributeError

    return 10


# *********************************************************************************
### Entrypoints
def handled():
    try:
        b = sub()
    except (IOError, AttributeError):
        b = 2

    return 1 + b


def unhandled():
    b = sub()

    return 1 + b
