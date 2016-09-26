# coding=utf8
from __future__ import unicode_literals
import pandas as pd
import re
import logging
from .unit_name_maps import name_maps
from .conversions_utils import insert_text_match_info_rows, clean_newlines
from .utils import Timer
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
                number_indices = match_info.loc[match_info.type == 'number', :].index.values
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
                            match_info['multipliable'].iloc[-2] = False
                            sister_idx = number_indices[-2]
                        else:
                            num_value = number_values[-1]
                            sister_idx = number_indices[-1]
                    else:
                        num_value = number_values[-1]
                        sister_idx = number_indices[-1]
                else:
                    num_value = number_values[0]
                    sister_idx = number_indices[0]

                info['sister_idx'] = int(sister_idx)
                match_info.loc[sister_idx, 'sister_idx'] = int(info.index.values[0])
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
    pattern = '|'.join(patterns)
    # prepend this pattern with a pattern for integers, floats, and simple fractions:
    float_pat = '\.?\d/\.?\d|\d+\.?\d+|\d+|\.\d+'
    pattern = '|'.join([float_pat, pattern])
    pattern = re.compile(pattern, re.IGNORECASE)

    # first, see if it's a list line:
    if re.match(pattern=r'^\s*[0-9]+\.?\s*$', string=line):
        match_info = pd.DataFrame(dict(start=0, end=len(line), name=line, multipliable=False,
                                       original=line, type='number', sub_type='line_number'),
                                  index=[0])
    else:
        original_line = line
        match_info = pd.DataFrame()
        placement = 0
        iter = 0
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
                                             pattern=float_pat, multipliable=True),
                                        index=[start+placement])
                else:
                    # otherwise, the row can be build off of the name_maps objects:
                    pidx = p.replace('.', '\.')
                    pidx = pidx if pidx in name_maps.index else pidx.lower()
                    # todo raise warning if p is still not in the index of name_maps

                    info = pd.DataFrame(name_maps.loc[pidx, :]).T
                    info.index = [start + placement]
                    info['original'] = p
                    info['start'] = start + placement
                    info['end'] = end + placement
                    info['pattern'] = pidx

                    match_info, info = handle_unit_plurality(info=info, match_info=match_info, pidx=start + placement)

                # record the info:
                placement = int(info.loc[:, 'end'])
                # todo change this to pd.append?
                match_info = pd.concat([match_info, info])
            else:
                end = len(line)
            iter += 1

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
        comparison = [match_info[columns[j]].iloc[i + j] for j in range(n_patterns)]
        if patterns == comparison and match_info.iloc[i + 1]['name'] in middle_name_matches:
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


def lookback_from_type_for_type(match_info, hit_type, lookback_type, new_sub_type,
                                dont_skip_over_type='unit', lookback=3, type_or_sub_type='type'):
    lookback += 1
    idx = match_info.loc[match_info[type_or_sub_type] == hit_type].index.values
    for i in idx:

        m = match_info.loc[:i, :]
        m = m.drop(m.index[-1])
        m = m.tail(lookback)
        if len(m) > 0:
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

    if any(match_info.index.duplicated()):
        logging.warning('DUPLICATED INDEX VALUES in match_info.')
    idx = [i for i in match_info.index if re.match(regex_pattern, match_info.loc[i, 'name'])]
    for i in idx:
        m = match_info.loc[:i, :].tail(lookback)
        is_number = m.type == lookback_type
        if any(is_number):
            hit = m.loc[is_number]
            hit = hit.index[-1]
            match_info.loc[hit, 'sub_type'] = new_sub_type

    return match_info


def lookforward_for_type_from_pattern(match_info, regex_pattern, lookback_type, new_sub_type, lookback=1):
    lookback += 1
    idx = [i for i in match_info.index if re.match(regex_pattern, match_info.loc[i, 'name'])]
    for i in idx:
        m = match_info.loc[i:, :].head(lookback)
        is_number = m.type == lookback_type
        if any(is_number):
            hit = m.loc[is_number].index[0]
            match_info.loc[hit, 'sub_type'] = new_sub_type

    return match_info


def replace_rows(match_info, idx, new_row):
    match_info = match_info.drop(match_info.index[idx])
    match_info = match_info.append(new_row)
    match_info = match_info.sort_index()

    return match_info


def replace_match_rows_with_aggregate(match_info, hits_gen, type, sub_type):
    for i in hits_gen:
        idx = [i, i + 1, i + 2]
        rows = match_info.iloc[idx, :]
        start = int(rows.end.iloc[0])
        new_row = pd.DataFrame(dict(start=start,
                                    end=rows.end.iloc[len(rows) - 1],
                                    name=''.join(rows.name),
                                    original=''.join(rows.original),
                                    type=type, sub_type=sub_type, sister_idx=rows.sister_idx.iloc[i]),
                               index=[start])

        # first one shouldn't be neccessary:
        match_info.loc[match_info.sister_idx == match_info.index[i], 'sister_idx'] = start
        match_info.loc[match_info.sister_idx == match_info.index[i+1], 'sister_idx'] = start
        match_info.loc[match_info.sister_idx == match_info.index[i+2], 'sister_idx'] = start

        match_info = replace_rows(match_info=match_info, idx=idx, new_row=new_row)

    return match_info


def tag_matches_from_line(match_info):

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
                                  middle_name_matches=[' - ', '-', ' to ', '- to ', ' or '])
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
                                             new_sub_type='temperature_number', dont_skip_over_type='unit', lookback=2,
                                             type_or_sub_type='sub_type')
    #######################################################################################################
    # tag time numbers
    match_info = lookback_from_type_for_type(match_info=match_info, hit_type='time', lookback_type='number',
                                             new_sub_type='time_number', dont_skip_over_type='unit', lookback=2,
                                             type_or_sub_type='sub_type')
    #######################################################################################################
    # tag length numbers
    match_info = lookback_from_type_for_type(match_info=match_info, hit_type='length', lookback_type='number',
                                             new_sub_type='length_number', dont_skip_over_type='unit', lookback=2,
                                             type_or_sub_type='sub_type')
    #######################################################################################################
    # tag percent numbers:
    match_info = lookback_for_type_from_pattern(match_info=match_info, regex_pattern=r'^[ ]?%| percent',
                                                lookback_type='number', lookback=2, new_sub_type='percent_number')
    #######################################################################################################
    # tag 'for each' numbers:
    # example: 1/2 cups at a time, or 1 teaspoon each
    # todo this isn't very specific, might not work / cause errors.
    each_pattern = r'^[, ]each|^ for each|^ pieces each|^ times|^ at a time|^ of'
    match_info = lookback_for_type_from_pattern(match_info=match_info,
                                                regex_pattern=each_pattern,
                                                lookback_type='number',
                                                new_sub_type='each_number', lookback=2)
    each_pattern = r'^ for each'
    match_info = lookforward_for_type_from_pattern(match_info=match_info,
                                                   regex_pattern=each_pattern,
                                                   lookback_type='number',
                                                   new_sub_type='each_number', lookback=1)
    # what about 'sprinkle each roll with 1/2 teaspoons sugar'?


    # todo


    # probably sub_types should be tags, instead, so that overlaps are caught....
    # ###### list of sub_types:
    # ## TEMPERATURE
    # temperature_number

    # ## UNIT OF TIME
    # time_number
    # ## number

    # # CONVERTIBLE:
    # int_fraction
    # int
    # float
    # fraction
    # unicode_fraction
    # english_number
    # range

    # # NOT CONVERTIBLE:
    # percent_number
    # package_size
    # each_number
    # dimensions

    # ## UNIT
    # weight
    # volume
    # pcs

    # ### list of types:
    # temperature
    # unit_of_time
    # unit
    # number
    # text

    return match_info


def parse_ingredient_line(line):
    with Timer(name='MATCHING {}'.format(line)) as t1:
        match_info = find_matches_in_line(line=line)

    with Timer(name='TAGGING {}'.format(line)) as t2:
        match_info = tag_matches_from_line(match_info=match_info)

    # match_info = find_matches_in_line(line=line)
    # match_info = tag_matches_from_line(match_info=match_info)

    # sort the data frame:
    match_info = match_info.sort_values(by='start')
    # coerce into a dictionary that can be turned into JSON later:
    match_info.index = [str(i) for i in match_info.start.values]
    match_info['multipliable'] = [str(i) for i in match_info.multipliable.values]
    match_info = match_info.fillna('').to_dict(orient='index')

    return match_info


def parse_ingredients(x):
    x = clean_newlines(x)
    lines = x.split('\n')

    results_dict = {str(i): parse_ingredient_line(lines[i]) for i in range(len(lines))}
    print(results_dict)
    return results_dict
