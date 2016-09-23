import collections


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
