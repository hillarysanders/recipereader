# coding=utf8
from __future__ import unicode_literals
import re
import logging
import pandas as pd
from .base_conversion_dicts import name_maps_numbers, name_maps_volume, name_maps_weight, name_maps
from .conversions_utils import insert_text_match_info_rows, clean_newlines

X = """2 1/4 cups all-purpose flour
1 teaspoon baking soda
1 teaspoon salt
1 cup (2 sticks) butter, softened
3/4 cup granulated sugar
3/4 cup packed brown sugar
1 teaspoon vanilla extract
2 large eggs
2 cups (12-oz. pkg.) NESTLÉ® TOLL HOUSE® Semi-Sweet Chocolate Morsels
1 cup chopped nuts"""


def handle_unit_plurality(info, match_info, pidx):

    # handle unit plurality
    if info.loc[pidx, 'type'] in ['volume', 'weight']:
        # was the last number != 1?
        is_plural = 'unknown'
        if len(match_info) > 0:
            if any(match_info.type == 'number'):
                m = match_info.loc[match_info.type == 'number', 'value'].values
                if len(m) > 1:
                    m = m[-1]
                else:
                    m = m[0]
                # if the most recent number was 1:
                if m == 1:
                    is_plural = False
                    info['name'] = info['singular']
                else:
                    is_plural = True
                    info['name'] = info['plural']
                info['is_plural'] = is_plural
        # if that didn't work:
        if is_plural not in [True, False]:
            # todo raise warning that plurality could not be found...
            info['name'] = info['original']

    return info


def parse_ingredient_line(line):
    # todo add in patterns and treatment for floats, e.g. 2.5 pounds.
    # todo change number treatment entirely so that it can appear next to words. e.g. 30g.
    # sooo... first look for numbers. Then loop through the rest of the text using this code?
    patterns = ['[ \(]{}s?[\) $]|^{} | {}$'.format(p, p, p) for p in name_maps.index]
    pattern = '|'.join(reversed(patterns))
    # prepend this pattern with a pattern for integers, floats, and simple fractions:
    float_pat = '\.?\d/\.?\d|\d+\.?\d+|\d+|\.\d+'
    pattern = '|'.join([float_pat, pattern])
    pattern = re.compile(pattern, re.IGNORECASE)
    # pattern = re.compile(pattern)

    original_line = line
    match_info = pd.DataFrame()
    placement = 0
    while len(line) > 0:
        match = pattern.search(line)
        if match:
            start = match.start()
            end = match.end()
            p = match.group()
            # first, trim off whitespace / parentheses from the pattern:
            if re.search('[\) ]$', p):
                p = p[:-1]
                end -= 1
            if re.search('^[\( ]', p):
                p = p[1:]
                start += 1

            # if it's a float pattern match, we build the row by hand
            if re.search(float_pat, p):
                if '/' in p:
                    value = p.split('/')
                    value = float(value[0]) / float(value[1])
                else:
                    value = float(p)

                info = pd.DataFrame(dict(start=start + placement, end=end + placement, name=p,
                                         original=p, value=value, type='number', pattern=float_pat),
                                    index=['number'])
            else:
                # otherwise, the row can be build off of the name_maps objects:
                # if p isn't in the index of name_maps, it probably has an s on the end:
                pidx = p if p in name_maps.index else p[:-1]
                # we want the start and end to stay the same but the pattern to forget the s.
                # todo raise warning if p is still not in the index of name_maps

                info = pd.DataFrame(name_maps.loc[pidx, :]).T
                info['original'] = p
                info['start'] = start + placement
                info['end'] = end + placement
                info['pattern'] = pidx

                info = handle_unit_plurality(info=info, match_info=match_info, pidx=pidx)

            # record the info:
            placement = info.loc[:, 'end'][0]
            # todo change this to pd.append?
            match_info = pd.concat([match_info, info])
        else:
            end = len(line)

        line = line[end:]

    match_info, original_line = insert_text_match_info_rows(match_info=match_info, original_line=original_line)

    match_info = match_info.sort_values(by='start')

    # todo add in sub-pattern flag of some sort
    # types:
    # amount
    # units

    # sub-types:
    # MULTIPLICATIVE:
    # - fraction
    # - float
    # - integer
    # OTHER
    # - degrees
    # - pre_fraction_integer
    # UNITS
    # - pcs ('package', 'scoops', etc.)
    # - volume, metric
    # - volume, imperial
    # - weight

    # todo flag fraction values as 'fraction'
    # todo flag units as 'unit' (value='pcs'), volume and weight = sub_types, type='unit'
    # todo run over rows and combine integer followed by ' ' followed by fraction

    match_info = match_info.sort_values(by='start')
    match_info.index = [str(i) for i in match_info.start.values]

    return match_info.fillna('').to_dict(orient='index')

# todo match to numbers not followed by 'times', other numbers,


def parse_ingredients(x):
    x = clean_newlines(x)
    lines = x.split('\n')
    results_dict = {str(i): parse_ingredient_line(lines[i]) for i in range(len(lines))}
    return results_dict