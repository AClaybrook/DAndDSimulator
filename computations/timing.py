""" Timing of the slow simulation entry points, in the log at DEBUG level (logging.getLogger("timing")) """
import logging
from functools import wraps
from time import perf_counter

log = logging.getLogger("timing")

def timeit(f):
    """ Decorator that logs how long a function took """
    @wraps(f)
    def wrap(*args, **kw):
        start = perf_counter()
        result = f(*args, **kw)
        log.debug("%s: %.4f sec", f.__name__, perf_counter() - start)
        return result
    return wrap
