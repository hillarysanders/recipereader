# coding=utf8
from __future__ import unicode_literals
import pandas as pd
import numpy as np
import re
from .unit_name_maps import name_maps, multipliable
from . import conversions_utils as conv_utils
from . import utils
from .unit_conversion_matrices import CONVERSION_FACTORS

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
                                             order=np.nan),
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
        match_info['sub_type'].iloc[i + 3] = 'package'
    # e.g. "1 (16 oz.) package"
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type', 'sub_type', 'type', 'type', 'sub_type'],
                                       patterns=['number', 'spacer', 'number', 'spacer', 'unit', 'spacer', 'pcs'],
                                       middle_name_matches=None)
    for i in idx:
        match_info['sub_type'].iloc[i + 2] = 'package_number'
        match_info['sub_type'].iloc[i + 4] = 'package'
    #######################################################################################################
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type'],
                                       patterns=['number', 'text', 'number'],
                                       middle_name_matches=[' - ', '-', ' to ', '- to ', ' or '])
    match_info = conv_utils.replace_match_rows_with_aggregate(match_info=match_info, hits_gen=idx,
                                                              type='number', sub_type='range')
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type'],
                                       patterns=['number', 'spacer', 'number'],
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
                                    'separator', 'start', 'end', 'plus_name', 'add_on'],
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
                    # print('UNIT PATTERN {}'.format( next_two.pattern.iloc[1]))
                    amounts.loc[i, 'unit_name'] = next_two.name.iloc[1]
                    amounts.loc[i, 'unit_pattern'] = next_two.pattern.iloc[1]
                    amounts.loc[i, 'unit_sub_type'] = next_two.sub_type.iloc[1]
                    amounts.loc[i, 'end'] = end + 1
                    amounts.loc[i, 'unit_idx'] = end

    return amounts


def change_servings_line(line, convert_sisterless_numbers, multiplier):

    # TODO work on cleaning up a bunch on uneccesary data and computation.

    amounts = conv_utils.json_dict_to_df(line['amounts'])
    match_info = conv_utils.json_dict_to_df(line['match_info'])

    if len(amounts) > 0:
        # now, merge any amounts that are meant to be together:
        side_by_side_idx = (amounts['start'].iloc[1:] - 1) == (amounts['end'].iloc[:-1])
        side_by_side_idx = reversed(side_by_side_idx.index[side_by_side_idx].values)
        for i in side_by_side_idx:
            if match_info['sub_type'].iloc[i - 1] == 'plus':
                i_pre = amounts.index[amounts.index.get_loc(i) - 1]
                to_merge = amounts.loc[[i_pre, i], :]
                new_row = to_merge.iloc[0, :]
                new_row.end = to_merge.end.iloc[1]
                new_row.plus_name = match_info['name'].iloc[i - 1]
                conversion_float = CONVERSION_FACTORS.conversions[to_merge.unit_name.iloc[1]][new_row.unit_name]
                new_row.number_value += to_merge.number_value.iloc[1] * conversion_float
                conv_utils.replace_rows(amounts, idx=[i_pre, i], new_row=new_row, by_iloc=False)

        for aidx in amounts.index:
            amount = amounts.loc[aidx, :]
            both_multipliable = multipliable.get(amount['number_sub_type']) and multipliable.get(amount['unit_sub_type'])
            sisterless_number = not isinstance(amount.get('unit_pattern'), str) and convert_sisterless_numbers

            if both_multipliable is True or sisterless_number:
                amount = conv_utils.multiply_amount(amount=amount, convert_to=None, multiplier=multiplier)

                # if value is below unit's threshold, convert to that unit.
                # if value is above unit's threshold, conver to that unit.
                if not sisterless_number:
                    if amount.number_sub_type != 'range':
                        unit_name = name_maps.loc[amount.unit_pattern, 'singular']
                        if amount.number_value < CONVERSION_FACTORS.thresholds[unit_name]['min']:
                            convert_to = CONVERSION_FACTORS.thresholds[unit_name]['smaller_unit']
                            amount = conv_utils.multiply_amount(amount=amount, convert_to=convert_to, multiplier=None)
                        elif amount.number_value >= CONVERSION_FACTORS.thresholds[unit_name]['max']:
                            convert_to = CONVERSION_FACTORS.thresholds[unit_name]['larger_unit']
                            amount = conv_utils.multiply_amount(amount=amount, convert_to=convert_to, multiplier=None)

                        # now, if decimal is below threshold, create a secondary amount:
                        decimal = amount.number_value % 1
                        unit_name = name_maps.loc[amount.unit_pattern, 'singular']
                        if 0 < decimal < CONVERSION_FACTORS.thresholds[unit_name]['min']:
                            convert_to = CONVERSION_FACTORS.thresholds[unit_name]['smaller_unit']
                            dec_multiplier = CONVERSION_FACTORS.conversions[unit_name][convert_to]
                            add_value = conv_utils.multiply_number(sub_type=amount.number_sub_type,
                                                                   number_val=decimal,
                                                                   multiplier=dec_multiplier)
                            add_unit_name = name_maps.loc[convert_to, conv_utils.get_plurality(add_value)]
                            amount['number_value'] = float(int(amount.number_value))
                            amount['number_name'] = str(int(amount.number_value))

                            insert_text_idx = match_info.end.iloc[amount.end]
                            # mi_row = pd.DataFrame(dict(), index=amount.start)
                            # todo instead of doing add on, make new match_info rows and insert them into match_info???
                            # dealeo is: you want to be able to change servings, and then STILL be able to do things
                            # like change units to metric.

                            add_on_start_end = match_info.loc[amount.start:amount.end, 'end'].iloc[-1]
                            mi_row = pd.DataFrame(dict(start=add_on_start_end, end=add_on_start_end,
                                                       order=[0, 1, 2, 3],
                                                       type=['plus', 'number', 'spacer', 'unit'],
                                                       pattern=[np.nan, np.nan, np.nan, convert_to],
                                                       sub_type=[np.nan, amount.number_sub_type,
                                                                 np.nan, amount.unit_sub_type],
                                                       value=[np.nan, dec_multiplier * decimal, np.nan, np.nan],
                                                       original='',
                                                       name=[' plus ', add_value, ' ', add_unit_name]),
                                                  index=[add_on_start_end, add_on_start_end,
                                                         add_on_start_end, add_on_start_end])
                            match_info = match_info.append(mi_row)

                if not sisterless_number:
                    match_info['name'].iloc[int(amount.unit_idx)] = name_maps.loc[amount.unit_pattern, 'singular']
                    match_info['pattern'].iloc[int(amount.unit_idx)] = amount.unit_pattern
                match_info['name'].iloc[amount.start] = amount.number_name
                match_info['value'].iloc[amount.start] = amount.number_value

    if 'order' not in match_info.columns:
        match_info.loc[:, 'order'] = np.nan
    match_info.loc[:, 'order'].replace(to_replace='', value=np.nan, inplace=True)

    match_info = match_info.sort_values(by='order', ascending=True, na_position='first')
    match_info = match_info.sort_index()

    new_amounts = get_amounts(match_info)
    match_info = conv_utils.update_plurality(match_info, new_amounts)

    if ' or so ' in match_info.name.values:
        print(''.join(match_info.name))
        # import pdb; pdb.set_trace()
    # coerce into a dictionary that can be turned into JSON later:
    match_info.index = [i for i in match_info.start.values]
    # match_info = conv_utils.df_to_json_ready_dict(match_info)
    # new_amounts = conv_utils.df_to_json_ready_dict(new_amounts)

    return dict(match_info=match_info, amounts=amounts)


def change_servings(ingredients, convert_sisterless_numbers, servings0, servings1):
    multiplier = float(servings1) / float(servings0)
    if multiplier == 1.:
        return ingredients

    results_dict = {str(i): change_servings_line(ingredients[i], multiplier=multiplier,
                                                 convert_sisterless_numbers=convert_sisterless_numbers) for i in
                    ingredients.keys()}

    return results_dict


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
    match_info = conv_utils.update_plurality(match_info, amounts)

    # coerce into a dictionary that can be turned into JSON later:
    match_info.index = [i for i in match_info.start.values]
    match_info = conv_utils.df_to_json_ready_dict(match_info)
    amounts = conv_utils.df_to_json_ready_dict(amounts)

    return dict(match_info=match_info, amounts=amounts)


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
