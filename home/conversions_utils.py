# coding=utf8
from __future__ import generators, unicode_literals
from .unit_name_maps import multipliable
import pandas as pd
import re


def change_servings(x, convert_sisterless_numbers, servings0, servings1):

    multiplier = float(servings1) / float(servings0)
    if multiplier == 1.:
        return x

    for line_number, line in x.items():
        idx = line.keys()

        # for each number:
            # if convert_sisterless_numbers:
                # if sister exists:
                    # yield sub_type, and sub_type of sister
                # else:
                    # yield sub_type
            # else:
                # if sister exists:
                    # yield sub_type, and sub_type of sister
                # else:
                    # don't yield

        df = pd.DataFrame.from_dict(line, orient='index')
        # import pdb; pdb.set_trace()
        # todo case where no sister_idx exists
        hits = [dict(key=k, number=v['sub_type'], unit=line[str(int(v['sister_idx']))]['sub_type']) for k, v in
                line.items() if v['type'] == 'number']
        for hit in hits:
            if multipliable[hit['number']] and multipliable[hit['unit']]:
                line[hit['key']]['name'] = multiply_number(number_val=line[hit['key']]['value'],
                                                           sub_type=line[hit['key']]['sub_type'],
                                                           multiplier=multiplier)

    return x


def multiply_number(sub_type, number_val, multiplier):

    def int_or_float(string):
        val = float(string)*multiplier
        if val % 1 == 0:
            val = int(val)
        return val

    if sub_type in ['range', 'int_fraction']:
        value = [int_or_float(v) for v in number_val.split(' ')]
    else:
        value = int_or_float(number_val)

    if sub_type == 'range':
        name = '{} to {}'.format(value[0], value[1])
    elif sub_type == 'int_fraction':
        name = '{} {}'.format(value)
    else:
        name = str(value)

    # todo implement larger method for changing decimal to fraction, and fraction to unicode fraction
    # todo then decide if e.g. certain units should always be converted down. e.g. 3 tps always = 1 tbsp.

    return name



# multipliable = dict(
#     temperature=False,
#     temperature_number=False,
#     length=False,
#     length_number=False,
#     percent=False,
#     percent_number=False,
#     time=False,
#     time_number=False,
#     package_size=False,
#     each_number=False,
#     dimension=False,
#     weight=True,
#     volume=True,
#     pcs=True,
#     int_fraction=True,
#     int=True,
#     fraction=True,
#     float=True,
#     unicode_fraction=True,
#     english_number=True,
#     range=True
# )


def insert_text_match_info_rows(match_info, original_line):
    nrows = len(match_info)
    nchars = len(original_line)
    if nrows == 0:
        match_info = pd.DataFrame(dict(type='text', name=original_line, original=original_line,
                                       start=0, end=nchars, sub_type='', sister_idx=None),
                                  index=[0])
    else:
        for i in range(nrows+1):
                if i == 0:
                    # look to the beginning of the line to the start of the first pattern (this pattern)
                    start = 0
                    end = match_info.iloc[i].start
                elif i >= nrows:
                    # look to the last of the last pattern to the end of the line
                    start = match_info.iloc[i-1]['end']
                    end = nchars
                else:
                    # look to the end of the last pattern to the start of this pattern
                    start = match_info.iloc[i-1]['end']
                    end = match_info.iloc[i].start

                if end > start:
                    text = original_line[start:end]
                    newrow = pd.DataFrame(dict(type='text', name=text, original=text, start=start, end=end,
                                               sub_type='', sister_idx=None),
                                          index=[start])
                    match_info = pd.concat([match_info, newrow])
                elif end < start:
                    raise Warning('End < start??? Indexing got messed up...')

    return match_info, original_line


def multiple_replace(pattern_replace_dict, text):
    """
    This function will take a dictionary of regex pattern: replacement key value pairs
    and perform  all of the replacements on the same string.
    It's handy when e.g. the replacement may be the same as a key, and you don't
    want to get into some silly recursive loop of finding and replacing things.
    """
    # Create a regular expression  from the dictionary keys:
    regex = re.compile("(%s)" % "|".join(map(re.escape, pattern_replace_dict.keys())))

    # For each match, look-up corresponding value in dictionary:
    return regex.sub(lambda mo: pattern_replace_dict[mo.string[mo.start():mo.end()]], text)


def clean_newlines(x):
    return x.replace('\r\n', '\n').replace('\r', '\n')


def _add_highlight(match_dict, type_or_sub_types=['type', 'sub_type'], prefix='<hi_{}>', postfix='</hi_{}>'):
    txt = match_dict['name']
    for key in type_or_sub_types:
        t = match_dict[key]
        txt = '{}{}{}'.format(prefix.format(t), txt, postfix.format(t))

    return txt


def sort_char_keys(d):
    return list(map(str, sorted(map(int, d.keys()))))


def get_highlighted_ingredients(parsed_text, type_or_sub_types=['type', 'sub_type']):
    """
    :param parsed_text: output of parse_ingredients()
    """
    idx = sort_char_keys(parsed_text)
    highlighted = []
    for i in idx:
        match_dicts = parsed_text[i]
        text = ''.join(_add_highlight(match_dicts[k],
                                      type_or_sub_types=type_or_sub_types) for k in sort_char_keys(match_dicts))
        highlighted.append(text)

    return highlighted


def KnuthMorrisPratt(text, pattern):

    '''Yields all starting positions of copies of the pattern in the text.
    Calling conventions are similar to string.find, but its arguments can be
    lists or iterators, not just strings, it returns all matches, not just
    the first one, and it does not need the whole text in memory at once.
    Whenever it yields, it will have read the text exactly up to and including
    the match that caused the yield.'''

    # allow indexing into pattern and protect against change during yield
    pattern = list(pattern)

    # build table of shift amounts
    shifts = [1] * (len(pattern) + 1)
    shift = 1
    for pos in range(len(pattern)):
        while shift <= pos and pattern[pos] != pattern[pos-shift]:
            shift += shifts[pos-shift]
        shifts[pos+1] = shift

    # do the actual search
    startPos = 0
    matchLen = 0
    for c in text:
        while matchLen == len(pattern) or \
              matchLen >= 0 and pattern[matchLen] != c:
            startPos += shifts[matchLen]
            matchLen -= shifts[matchLen]
        matchLen += 1
        if matchLen == len(pattern):
            yield startPos