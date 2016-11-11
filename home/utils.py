import collections
import time
import numpy as np
import pandas as pd


def png_premultiply(im):
    pixels = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = pixels[x, y]
            if a != 255:
                r = r * a // 255
                g = g * a // 255
                b = b * a // 255
                pixels[x, y] = (r, g, b, a)

    return im


def png_unmultiply(im):
    pixels = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            r, g, b, a = pixels[x, y]
            if a != 255 and a != 0:
                r = 255 if r >= a else 255 * r // a
                g = 255 if g >= a else 255 * g // a
                b = 255 if b >= a else 255 * b // a
                pixels[x, y] = (r, g, b, a)

    return im


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


def subset(x, idx, recursive=True):
    """
    :param x: a list of values of length n
    :param idx: a list of Boolean (True, False) values of length n
    :param recursive: Boolean. Allow recursive subsetting?

    :return: a list of all x values for which the corresponding Boolean
        value (x[i] <--> idx[i]) was True

    Note that subset retains embedded lists structure. Use flatten_lists if you wish
    to flatten / unroll your results. If your x and idx do not contain embedded lists, subset(recursive=True)
    will function the same as subset(recursive=False), but the latter will
    be a bit faster. If recursive = True, then subset will be applied to each
    sub list.
    Unless idx and x have the same structure, an error
    will be thrown (for the most part - e.g. if  x is e.g. [1,2,3] at a node,
    and idx is False at not node instead of e.g. [True, False, True], the entire
    node in x will be excluded with no error. If there is a conflict at an actual node
    level though, e.g. if x is [1,2,3] and idx is [True, False], or idx is [True, False]
    and x is [1] then this will throw an error.)
    x is e.g. [1,2,3] and that node, then that node will be deleted.


    Example:
        import numpy as np
        idx = [True, False, np.nan, True]
        x = [1,2,3,4]
        subset(x, idx)
        # returns: [1,4]

    """
    if recursive:
        embedded_lists_idx = [isinstance(el, list) for el in idx]
        idx_top = which(idx)
        return [subset(x[i], idx[i], recursive=True) if embedded_lists_idx[i] is True else x[i] for i in idx_top]
    else:
        return [x[i] for i in range(len(x)) if idx[i] is True]


def non_null(li):
    """
    Removes none and nan elements from a list. Use pd.dropna for pandas series.
    Not recursive (TODO (hills): add optional recursion?)
    Returns a pd series.
    :param li: list of values
    :return: list of non-null values, depending on input type of li
    """

    idx = (~pd.isnull(li)).astype(list)
    clean = subset(li, idx, recursive=False)

    return clean


def which(li):
    """
    :param li: list of boolean values
    :return: indices of True values in li
    """
    n = range(len(li))
    return [i for i in n if li[i]]


def unique(li):
    """
    Like set() but preserves order, which is sometimes handy.
    :param li: a list of values
    :return: unique values in li
    """
    seen = set()
    seen_add = seen.add
    return [x for x in li if not (x in seen or seen_add(x))]


def which_max(li):
    """
    Returns the index of the maximum value in a list
    If there are more than one maximum values, the
    lowest index is returned.
    :param li:
    :return: integer - index of the max value in li

    Example:
    which_max([0,1,2,3,10,10,6])
    # returns 4
    """
    if not isinstance(li, list):
        li = list(li)
    idx = max(range(len(li)), key=lambda i: li[i])
    return idx


def which_min(li):
    """
    Returns the index of the minimum value in a list
    If there are more than one minimum value, the
    lowest index is returned
    :param li:
    :return: integer - index of the max value in li

    Example:
    which_min([0,1,2,3,-1,-1,6])
    # returns 4
    """
    if not isinstance(li, list):
        li = list(li)
    idx = min(range(len(li)), key=lambda i: li[i])
    return idx


def is_in(x, y):
    """
    :param x: a list of values of length n
    :param y: a list of values of any length
    :return: a list of Boolean values, corresponding to if
     each value in x is in y.

    Example:
    x = [1,15,[1,2,3],'a', 'Sandy', {'a':[4]}]
    y = [[1,2,3], 15, 'Sand', {'a':[4]}]
    is_in(x,y)
    # returns:
    # [False, True, True, False, False, True]
    """
    idx = [xx in y for xx in x]
    return idx
