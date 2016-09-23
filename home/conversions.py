# coding=utf8
from __future__ import unicode_literals
import pandas as pd
import re
from .unit_name_maps import name_maps
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
    if info.loc[pidx, 'type'] in ['unit']:
        # was the last number != 1?
        is_plural = 'unknown'
        if len(match_info) > 0:
            numeric_idx = match_info.type == 'number'
            if any(numeric_idx):
                number_values = match_info.loc[match_info.type == 'number', 'value'].values
                if sum(numeric_idx) > 1:
                    # todo (low priority) might want to add something to the below that marks this as unsure if e.g.
                    # todo you have a ['number', 'unit', 'number'] pattern or something.

                    # so usually, we just want the nearest number to the left.
                    # however, what about e.g. "1 (16oz.) container yogurt"?
                    # if there is another unit to the left, and then two numbers, take the first number.
                    if len(match_info) >= 3:
                        if all(match_info.type.tail(3) == ['number', 'number', 'unit']):
                            # "1 (16oz.) container yogurt" case
                            num_value = match_info['value'].iloc[-3]
                            match_info['sub_type'].iloc[-2] = 'package_size'
                        else:
                            num_value = number_values[-1]
                    else:
                        num_value = number_values[-1]
                else:
                    num_value = number_values[0]
                # if the most recent number was 1:
                if num_value == 1:
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

    return match_info, info


def find_matches_in_line(line):
    ok_left = '[- \(]'
    ok_right = '[- \)\.,]'
    # sooo... first look for numbers. Then loop through the rest of the text using this code?
    patterns = [(ok_left + '{}' + ok_right + '|^{}' + ok_right + '|' + ok_left + '{}$|^{}$').format(p, p, p, p) for p in
                name_maps.index]
    pattern = '|'.join(reversed(patterns))
    # prepend this pattern with a pattern for integers, floats, and simple fractions:
    float_pat = '\.?\d/\.?\d|\d+\.?\d+|\d+|\.\d+'
    pattern = '|'.join([float_pat, pattern])
    pattern = re.compile(pattern, re.IGNORECASE)

    # first, see if it's a list line:
    if re.match(pattern=r'^\s*[0-9]+\.?\s*$', string=line):
        match_info = pd.DataFrame(dict(start=0, end=len(line), name=line,
                                       original=line, type='number', sub_type='line_number'),
                                  index=['number'])
    else:
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
                if re.search(ok_right + '$', p):
                    p = p[:-1]
                    end -= 1
                if re.search('^' + ok_left, p):
                    p = p[1:]
                    start += 1

                # if it's a float pattern match, we build the row by hand
                if re.search(float_pat, p):
                    if '/' in p:
                        value = p.split('/')
                        value = float(value[0]) / float(value[1])
                        sub_type = 'fraction'
                    else:
                        value = float(p)
                        if (value % 1) == 0:
                            sub_type = 'int'
                        else:
                            sub_type = 'float'

                    info = pd.DataFrame(dict(start=start + placement, end=end + placement, name=p,
                                             original=p, value=value, type='number', sub_type=sub_type,
                                             pattern=float_pat),
                                        index=['number'])
                else:
                    # otherwise, the row can be build off of the name_maps objects:
                    pidx = p.replace('.', '\.')
                    pidx = pidx if pidx in name_maps.index else pidx.lower()
                    # todo raise warning if p is still not in the index of name_maps

                    info = pd.DataFrame(name_maps.loc[pidx, :]).T
                    info['original'] = p
                    info['start'] = start + placement
                    info['end'] = end + placement
                    info['pattern'] = pidx

                    match_info, info = handle_unit_plurality(info=info, match_info=match_info, pidx=pidx)

                # record the info:
                placement = info.loc[:, 'end'][0]
                # todo change this to pd.append?
                match_info = pd.concat([match_info, info])
            else:
                end = len(line)

            line = line[end:]

        # for all the text that wasn't tagged above as some special type (number, unit, etc)
        # what remains will just be tagged as 'text' for now.
        match_info, original_line = insert_text_match_info_rows(match_info=match_info, original_line=original_line)

    match_info = match_info.sort_values(by='start')

    return match_info


def find_type_pattern(match_info, n, columns, patterns, middle_name_matches):
    i = 0
    n_patterns = len(patterns)
    while (i + n_patterns) < n:
        comparison = [match_info.loc[i + j, columns[j]] for j in range(n_patterns)]
        if patterns == comparison and match_info.loc[i + 1, 'name'] in middle_name_matches:
            match = i
            i += n_patterns
            yield match
        else:
            i += 1


# def find_fraction_pattern(match_info, n):
#     columns = ['sub_type', 'type', 'sub_type']
#     patterns = ['int', 'text', 'fraction']
#
#     i = 0
#     n_patterns = len(patterns)
#     while (i+n_patterns) < n:
#         comparison = [match_info.loc[i+j, columns[j]] for j in range(n_patterns)]
#         if patterns == comparison and match_info.loc[i+1, 'name'] in [' ', ' and ', ' & ', ' + ']:
#             match = i
#             i += n_patterns
#             yield match
#         else:
#             i += 1


def replace_rows(match_info, idx, new_row):
    match_info = match_info.drop(idx)
    match_info = match_info.append(new_row)
    match_info = match_info.sort_index()
    match_info.index = range(len(match_info))

    return match_info


def lookback_from_type_for_type(match_info, hit_type, lookback_type, new_sub_type,
                                dont_skip_over_type='unit', lookback=3):
    lookback += 1
    idx = match_info.loc[match_info.type == hit_type].index.values
    for i in idx:
        m = match_info.loc[:i, :].tail(lookback)
        # cut off anything before a unit, though:
        unit_location = m.loc[m.type == dont_skip_over_type].index.max()
        if isinstance(unit_location, int):
            m = m.iloc[m.index.get_loc(unit_location):, :]

        is_number = m.type == lookback_type
        if any(is_number):
            hit = m.loc[is_number].index[-1]
            match_info.loc[hit, 'sub_type'] = new_sub_type

    return match_info


def lookback_for_type_from_pattern(match_info, regex_pattern, lookback_type, new_sub_type, lookback=3):
    lookback += 1
    idx = [i for i in match_info.index if re.match(regex_pattern, match_info.name.iloc[i])]
    for i in idx:
        m = match_info.loc[:i, :].tail(lookback)
        is_number = m.type == lookback_type
        if any(is_number):
            hit = m.loc[is_number].index[-1]
            match_info.loc[hit, 'sub_type'] = new_sub_type

    return match_info


def replace_match_rows_with_aggregate(match_info, hits_gen, type, sub_type):
    for i in hits_gen:
        idx = [i, i + 1, i + 2]
        rows = match_info.loc[idx, :]
        new_row = pd.DataFrame(dict(start=rows.end.iloc[0],
                                    end=rows.end.iloc[len(rows) - 1],
                                    name=''.join(rows.name),
                                    original=''.join(rows.original),
                                    type=type, sub_type=sub_type), index=[i])
        match_info = replace_rows(match_info=match_info, idx=idx, new_row=new_row)

    return match_info


def tag_matches_from_line(match_info):
    # todo add in sub-pattern flag of some sort
    # types:
    # amount
    # units

    match_info.index = range(len(match_info))

    # todo e.g. int_fraction, number_range, and dimension_numbers are all being overwritten.
    # todo I think we need to redesign this a bit to support tags. Also, it's starting to get slow. --> Bad!
    #######################################################################################################
    # tag fractions
    fraction_idx = find_type_pattern(match_info=match_info, n=len(match_info),
                                     columns=['sub_type', 'type', 'sub_type'],
                                     patterns=['int', 'text', 'fraction'],
                                     middle_name_matches=[' ', ' and ', ' & ', ' + '])
    match_info = replace_match_rows_with_aggregate(match_info=match_info, hits_gen=fraction_idx,
                                                   type='number', sub_type='int_fraction')
    #######################################################################################################
    # tag ranges:
    range_idx = find_type_pattern(match_info=match_info, n=len(match_info),
                                  columns=['type', 'type', 'type'],
                                  patterns=['number', 'text', 'number'],
                                  middle_name_matches=[' - ', '-', ' to ', '- to '])
    match_info = replace_match_rows_with_aggregate(match_info=match_info, hits_gen=range_idx,
                                                   type='number', sub_type='number_range')
    #######################################################################################################
    # tag dimensions (e.g. 12x9 inches):
    dims_idx = find_type_pattern(match_info=match_info, n=len(match_info),
                                 columns=['type', 'type', 'type'],
                                 patterns=['number', 'text', 'number'],
                                 middle_name_matches=[' x ', 'x', ' X ', 'X'])
    match_info = replace_match_rows_with_aggregate(match_info=match_info, hits_gen=dims_idx,
                                                   type='number', sub_type='dimension_numbers')
    #######################################################################################################
    # tag temperature numbers
    match_info = lookback_from_type_for_type(match_info=match_info, hit_type='temperature', lookback_type='number',
                                             new_sub_type='temperature_number', dont_skip_over_type='unit', lookback=2)
    #######################################################################################################
    # tag time numbers
    match_info = lookback_from_type_for_type(match_info=match_info, hit_type='unit_of_time', lookback_type='number',
                                             new_sub_type='time_number', dont_skip_over_type='unit', lookback=2)
    #######################################################################################################
    # tag length numbers
    match_info = lookback_from_type_for_type(match_info=match_info, hit_type='unit_of_length', lookback_type='number',
                                             new_sub_type='length_number', dont_skip_over_type='unit', lookback=2)
    #######################################################################################################
    # tag percent numbers:
    match_info = lookback_for_type_from_pattern(match_info=match_info, regex_pattern=r'^[ ]?%| percent',
                                                lookback_type='number', lookback=2, new_sub_type='percent_number')
    #######################################################################################################
    # tag 'for each' numbers:
    # example: 1/2 cups at a time, or 1 teaspoon each
    # todo this isn't very specific, might not work / cause errors.
    each_pattern = r'[, ]each| for each one| pieces each| times| at a time'
    match_info = lookback_for_type_from_pattern(match_info=match_info,
                                                regex_pattern=each_pattern,
                                                lookback_type='number',
                                                new_sub_type='each_number', lookback=3)
    each_pattern = r' of the'
    match_info = lookback_for_type_from_pattern(match_info=match_info,
                                                regex_pattern=each_pattern,
                                                lookback_type='number',
                                                new_sub_type='each_number', lookback=1)
    # what about 'sprinkle each roll with 1/2 teaspoons sugar'?

    # what about number ranges? e.g. 4-5. Both numbers should have the same sub_type. And probably they should be
    # joined, in fact. Before any other pattern matching takes place. Hmmmm. This could definitely cause some
    # sub_type doubling.


    # probably sub_types should be tags, instead, so that overlaps are caught....

    # ### list of sub_types:
    # temperature_number
    # time_number
    # int_fraction
    # percent_number
    # package_size
    # int
    # float
    # fraction
    # unicode_fraction
    # weight
    # volume
    # pcs
    # english_number
    # each_number

    # ### list of types:
    # temperature
    # unit_of_time
    # unit
    # number
    # text

    # flag integers vs fractions


    # sub-types:
    # MULTIPLICATIVE:
    # - fraction
    # - float
    # - integer
    # OTHER
    # - degrees
    # - pre_fraction_integer
    # - step_number (1., 2., 3....)
    # - percent, e.g. '2%'
    # UNITS
    # - pcs ('package', 'scoops', etc.)
    # - volume, metric
    # - volume, imperial
    # - weight
    # TEXT
    # - ingredient
    # - header
    # - text

    # todo flag fraction values as 'fraction'
    # todo flag units as 'unit' (value='pcs'), volume and weight = sub_types, type='unit'
    # todo run over rows and combine integer followed by ' ' followed by fraction

    return match_info


def parse_ingredient_line(line):
    match_info = find_matches_in_line(line=line)
    match_info = tag_matches_from_line(match_info=match_info)

    # sort the data frame:
    match_info = match_info.sort_values(by='start')
    # coerce into a dictionary that can be turned into JSON later:
    match_info.index = [str(i) for i in match_info.start.values]
    match_info = match_info.fillna('').to_dict(orient='index')

    return match_info


def parse_ingredients(x):
    x = clean_newlines(x)
    lines = x.split('\n')
    results_dict = {str(i): parse_ingredient_line(lines[i]) for i in range(len(lines))}
    return results_dict
