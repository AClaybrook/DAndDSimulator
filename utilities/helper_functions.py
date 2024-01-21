""" Generic helper functions """
from functools import wraps
from time import time

def timeit(f, print_=True):
    """ Decorator to time a function"""
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        if print_:
            print(f'{f.__name__}: {te-ts:2.4f} sec')
        return result
    return wrap
