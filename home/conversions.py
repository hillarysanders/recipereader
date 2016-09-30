# coding=utf8
from __future__ import unicode_literals
import pandas as pd
import numpy as np
import re
import logging
from .unit_name_maps import name_maps
from . import conversions_utils as conv_utils
from . import utils

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


# def handle_unit_plurality(info, match_info, pidx):
#     """
#     THIS CURRENTLY DOESN'T WORK GREAT BECAUSE IT TOTALLY IGNORES TEXT, SO IT CAN SKIP OVER A LOT. e.g.:
#     "Put 16 apples in the pot. Package up each piece of butter."
#     IS CHANGED TO:
#     "Put 16 apples in the pot. Packages up each pieces of butter."
#     """
#     # handle unit plurality
#     if info.loc[pidx, 'type'] in ['unit']:
#         if multipliable[info.loc[pidx, 'sub_type']]:
#             # was the last number != 1?
#             is_plural = 'unknown'
#             if len(match_info) > 0:
#                 numeric_idx = match_info.type == 'number'
#                 if any(numeric_idx):
#                     number_indices = match_info.loc[match_info.type == 'number', :].index.values
#                     number_values = match_info.loc[match_info.type == 'number', 'value'].values
#                     if sum(numeric_idx) > 1:
#                         # todo (low priority) might want to add something to the below that marks this as unsure if e.g.
#                         # todo you have a ['number', 'unit', 'number'] pattern or something.
#
#                         # so usually, we just want the nearest number to the left.
#                         # however, what about e.g. "1 (16oz.) container yogurt"?
#                         # if there is another unit to the left, and then two numbers, take the first number.
#                         if len(match_info) >= 3:
#                             if all(match_info.type.tail(3) == ['number', 'number', 'unit']):
#                                 # "1 (16oz.) container yogurt" case
#                                 num_value = match_info['value'].iloc[-3]
#                                 match_info['sub_type'].iloc[-2] = 'package_number'
#                                 sister_idx = number_indices[-2]
#                             else:
#                                 num_value = number_values[-1]
#                                 sister_idx = number_indices[-1]
#                         else:
#                             num_value = number_values[-1]
#                             sister_idx = number_indices[-1]
#                     else:
#                         num_value = number_values[0]
#                         sister_idx = number_indices[0]
#
#                     info['sister_idx'] = int(sister_idx)
#                     match_info.loc[sister_idx, 'sister_idx'] = int(info.index.values[0])
#                     # if the most recent number was 1:
#                     if num_value == 1:
#                         is_plural = False
#                         info['name'] = info['singular']
#                     else:
#                         is_plural = True
#                         info['name'] = info['plural']
#                     info['is_plural'] = is_plural
#             # if that didn't work:
#             if is_plural not in [True, False]:
#                 # todo raise warning that plurality could not be found...
#                 info['name'] = info['original']
#         else:
#             info['name'] = info['original']
#
#     return match_info, info


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
        match_info = pd.DataFrame(dict(start=0, end=len(line), name=line,
                                       original=line, type='text', sub_type='line_number'),
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
                                             pattern=float_pat),
                                        index=[start + placement])
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


                    # TODO TEMPORARY:
                    info['name'] = p
                    # match_info, info = handle_unit_plurality(info=info, match_info=match_info, pidx=start + placement)

                # record the info:
                placement = int(info.loc[:, 'end'])
                match_info = match_info.append(info, ignore_index=False)
            else:
                end = len(line)
            iter += 1

            line = line[end:]

        # for all the text that wasn't tagged above as some special type (number, unit, etc)
        # what remains will just be tagged as 'text' for now.
        match_info, original_line = conv_utils.insert_text_match_info_rows(match_info=match_info,
                                                                           original_line=original_line)

    match_info = match_info.sort_values(by='start')

    return match_info


def tag_matches_from_line(match_info):
    #######################################################################################################
    # tag fractions
    fraction_idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                                columns=['sub_type', 'type', 'sub_type'],
                                                patterns=['int', 'text', 'fraction'],
                                                middle_name_matches=[' ', ' and ', ' & ', ' + '])
    match_info = conv_utils.replace_match_rows_with_aggregate(match_info=match_info, hits_gen=fraction_idx,
                                                              type='number', sub_type='int_fraction',
                                                              value_func=lambda x, y: sum([x, y]))
    #######################################################################################################
    # # tag spaces as spacers:
    match_info.loc[[re.match(pattern='^[- \)\(\.,]+(or so)? ?$', string=n) is not None for n in match_info.name],
                   'type'] = 'spacer'
    match_info.loc[[re.match(pattern='^(,? and |,? ?\+ ?|,? plus )$', string=n) is not None for n in match_info.name],
                   'sub_type'] = 'plus'
    #######################################################################################################
    # ### tag 1 (16 oz) package numbers:
    # e.g. "1 (16oz.) package"
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type', 'type', 'type', 'sub_type'],
                                       patterns=['number', 'spacer', 'number', 'unit', 'spacer', 'pcs'],
                                       middle_name_matches=None)
    for i in idx:
        match_info['sub_type'].iloc[i + 2] = 'package_number'
        match_info['sub_type'].iloc[i + 3] = 'package_unit'
    # e.g. "1 (16 oz.) package"
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type', 'sub_type', 'type', 'type', 'sub_type'],
                                       patterns=['number', 'spacer', 'number', 'spacer', 'unit', 'spacer', 'pcs'],
                                       middle_name_matches=None)
    for i in idx:
        match_info['sub_type'].iloc[i + 2] = 'package_number'
        match_info['sub_type'].iloc[i + 4] = 'package_unit'
    #######################################################################################################
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type'],
                                       patterns=['number', 'text', 'number'],
                                       middle_name_matches=[' - ', '-', ' to ', '- to ', ' or '])
    match_info = conv_utils.replace_match_rows_with_aggregate(match_info=match_info, hits_gen=idx,
                                                              type='number', sub_type='range')

    # # tag multi-unit ingredients (e.g. 3 tablespoons plus 1 teaspoon sugar
    # range_idx = find_type_pattern(match_info=match_info, n=len(match_info),
    #                               columns=['type', 'sub_type', 'type', 'type', 'type', 'sub_type', 'type'],
    #                               patterns=['number', 'space', 'unit', 'text', 'number', 'space', 'unit'],
    #                               middle_name_matches=[', plus ', ' plus ', ' + ', '+', ' and ', ' & '])
    # match_info = replace_match_rows_with_aggregate(match_info=match_info, hits_gen=range_idx,
    #                                                type='number', sub_type='range')
    #######################################################################################################
    # tag dimensions (e.g. 12x9 inches):
    dims_idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                            columns=['type', 'type', 'type'],
                                            patterns=['number', 'text', 'number'],
                                            middle_name_matches=[' x ', 'x', ' X ', 'X'])
    match_info = conv_utils.replace_match_rows_with_aggregate(match_info=match_info, hits_gen=dims_idx,
                                                              type='number', sub_type='dimension')
    #######################################################################################################
    # tag numbers that go with odd unit types:
    # todo: is it even necessary to flag these here? I think probably not. Remove once other stuff is working.
    for unit_type in ['temperature', 'time', 'length', 'percent']:
        match_info = conv_utils.lookback_from_type_for_type(match_info=match_info, hit_type=unit_type,
                                                            lookback_type='number',
                                                            new_sub_type='{}_number'.format(unit_type),
                                                            dont_skip_over_type='unit',
                                                            lookback=2, type_or_sub_type='sub_type')
        # temperature_number, time_number, and length_number, percent_number
    #######################################################################################################
    # tag 'for each' numbers:
    # example: 1/2 cups at a time, or 1 teaspoon each
    # todo this isn't very specific, might not work / cause errors.
    each_pattern = r'^[, ]each|^ for each|^ pieces each|^ times|^ at a time|^ of'
    match_info = conv_utils.lookback_for_type_from_pattern(match_info=match_info,
                                                           regex_pattern=each_pattern,
                                                           lookback_type='number',
                                                           new_sub_type='each_number', lookback=2)

    return match_info


def get_amounts(match_info):
    numbers_idx = utils.which(match_info.type.values == 'number')
    amounts = pd.DataFrame(columns=['number_name', 'number_value', 'number_sub_type',
                                    'unit_name', 'unit_sub_type', 'unit_idx', 'unit_pattern',
                                    'separator', 'start', 'end', 'plus_name'],
                           index=numbers_idx)
    if len(numbers_idx) > 0:
        amounts.number_value = match_info.value.iloc[numbers_idx].values
        amounts.number_name = match_info.name.iloc[numbers_idx].values
        amounts.number_sub_type = match_info.sub_type.iloc[numbers_idx].values
        for i in numbers_idx:
            next_two = match_info.iloc[i:, :].head(3)
            amounts.loc[i, 'start'] = i
            amounts.loc[i, 'end'] = i + 1
            if len(next_two) > 1:
                if conv_utils.df_get(next_two, 1, 'type') == 'spacer':
                    amounts.loc[i, 'separator'] = conv_utils.df_get(next_two, 1, 'name')
                    next_two = next_two.iloc[[0, 2], :]
                    end = i + 2
                else:
                    end = i + 1
                if conv_utils.df_get(next_two, 1, 'type') == 'unit':
                    amounts.loc[i, 'unit_name'] = next_two.name.iloc[1]
                    amounts.loc[i, 'unit_pattern'] = next_two.pattern.iloc[1]
                    amounts.loc[i, 'unit_sub_type'] = next_two.sub_type.iloc[1]
                    amounts.loc[i, 'end'] = end + 1
                    amounts.loc[i, 'unit_idx'] = end

    return amounts


def update_plurality(match_info, amounts):
    for i in amounts.index[~amounts.isnull().unit_idx]:
        row = amounts.loc[i, :]
        # a number is plural if it is 1, or is a fraction whose numerator is one.
        # therefore:
        if row.number_sub_type == 'range':
            number_name = conv_utils.number_to_string(float(row.number_value.split(' ')[-1]))
        else:
            number_name = row.number_name

        if re.match('^(one|a |1/|⅛|⅙|⅓|⅕|¼|½|1$)', number_name, flags=re.IGNORECASE):
            column = 'singular'
        else:
            column = 'plural'

        unit_name = name_maps.loc[row['unit_pattern'], column]
        if unit_name == '':
            unit_name = row['unit_name']
        match_info['name'].iloc[row['unit_idx']] = unit_name

    return match_info


def parse_ingredient_line(line):
    with utils.Timer(name='MATCHING {}'.format(line), verbose=False) as t1:
        match_info = find_matches_in_line(line=line)

    with utils.Timer(name='TAGGING {}'.format(line), verbose=False) as t2:
        match_info = tag_matches_from_line(match_info=match_info)

    # match_info = find_matches_in_line(line=line)
    # match_info = tag_matches_from_line(match_info=match_info)

    # sort the data frame:
    match_info = match_info.sort_values(by='start')

    amounts = get_amounts(match_info)
    match_info = update_plurality(match_info, amounts)

    # coerce into a dictionary that can be turned into JSON later:
    match_info.index = [str(i) for i in match_info.start.values]
    match_info = match_info.fillna('').to_dict(orient='index')

    return match_info


def parse_ingredients(x):
    x = conv_utils.clean_newlines(x)
    lines = x.split('\n')

    results_dict = {str(i): parse_ingredient_line(lines[i]) for i in range(len(lines))}

    return results_dict


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
    # package
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
