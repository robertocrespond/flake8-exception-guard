from other_code import xyz
import random

entrypoint = lambda f: f

def sub() -> int:
    aaa = .5

    if random.random() < aaa:
        raise IOError
    
    return 10 + sub2()

def sub2() -> int:
    roberto = 100 
    if roberto > 101:
        raise AttributeError
    return roberto

class Rob:
    def do_something(self):
        raise ImportError

# d = Rob()

@entrypoint
def abc():
    # a = sub()

    def do_something2():
        raise AttributeError
    

    do_something2()

    # try:
    #     b = sub()
    # except (IOError):
    #     b = 2
    # try:
    #     d.do_something()
    # except (UnicodeError, ZeroDivisionError, ValueError):
    #     pass
    return 1 + 2
