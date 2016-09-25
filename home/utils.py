import collections
import time
import numpy as np

def flatten(l):
    """
    Recursively flatten a list of lists (of lists of lists, etc).
    :return: a generator object. Apply list() to coerce to a flat list.

    :example:
        li = [['a', 'b'], 'c', ['d', 'e', ['f', 'g', ['h']]]]
        list(flatten(li))
        # returns ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    """

    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el


def most_common(li):
    """
    Returns the most common element in a list (mode)
    :param li: a list
    :return: most common element in li
    WARNING: can't handle embedded lists
    """
    if not isinstance(li, list):
        li = list(li)
    return max(set(li), key=li.count)


class Timer(object):
    def __init__(self, verbose=True, name=''):
        self.verbose = verbose
        self.name = name

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000  # milliseconds
        if self.verbose:
            print('Elapsed time: {} seconds ({})'.format(np.round(self.secs, 2), self.name[:20]+'...'))
