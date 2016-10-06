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
                                  index=[0.])
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
                                             original=p, value=value, type='number', sub_type=sub_type),
                                        index=[float(start + placement)])
                else:
                    # otherwise, the row can be build off of the name_maps objects:
                    pidx = p.replace('.', '\.')
                    pidx = pidx if pidx in name_maps.index else pidx.lower()
                    # todo raise warning if p is still not in the index of name_maps

                    info = pd.DataFrame(name_maps.loc[pidx, :]).T
                    info.index = [float(start + placement)]
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
                                       columns=['type', 'type', 'type', 'type', 'type', 'type', 'sub_type'],
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
                                                              type='number', sub_type='range',
                                                              value_func=lambda val0, val2: '{} {}'.format(val0, val2))
    idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                       columns=['type', 'type', 'type'],
                                       patterns=['number', 'spacer', 'number'],
                                       middle_name_matches=[' - ', '-', ' to ', '- to ', ' or '])
    match_info = conv_utils.replace_match_rows_with_aggregate(match_info=match_info, hits_gen=idx,
                                                              type='number', sub_type='range',
                                                              value_func=lambda val0, val2: '{} {}'.format(val0, val2))
    #######################################################################################################
    # tag dimensions (e.g. 12x9 inches):
    dims_idx = conv_utils.find_type_pattern(match_info=match_info, n=len(match_info),
                                            columns=['type', 'type', 'type'],
                                            patterns=['number', 'text', 'number'],
                                            middle_name_matches=[' x ', 'x', ' X ', 'X'])
    match_info = conv_utils.replace_match_rows_with_aggregate(match_info=match_info, hits_gen=dims_idx,
                                                              type='number', sub_type='dimension')
    #######################################################################################################
    # tag 'for each' numbers:
    # example: "1/2 cups at a time", or "1 teaspoon each", or "spread about 1 teaspoon icing over each cupcake"
    # up to one word followed by one of these phrases (e.g. "3 leaves for each cupcake").
    each_pattern = r'^[ ,]?[^\s\.]*[, ]?(each|for each|pieces each|times|at a time|over each)'
    match_info = conv_utils.lookback_for_type_from_pattern(match_info=match_info,
                                                           regex_pattern=each_pattern,
                                                           lookback_type='number',
                                                           dont_skip_over_type='text',
                                                           new_sub_type='each_number', lookback=3)

    # todo maybe this should be applied to amounts, since e.g. you can have:
    # number spacer unit ' at a time'
    # number unit ' at a time'
    # number ' at a time'
    return match_info


def get_amounts(match_info):
    """
    This function looks through match_info tagged phrases and identifies ingredient 'amounts'.
    Amounts are defined as number types, optionally followed by a spacer type, optionally followed
    by a unit type. Resultant amounts contain the following potential sequences:
    - number
    - number unit
    - number spacer unit
    Note that the indices of the resultant amounts data frame will be the indices of the start-phrases in match_info.
    :param match_info:
    :return: amounts data frame
    """
    numbers_idx = match_info.index[match_info.type.values == 'number']
    amounts = pd.DataFrame(columns=['number_value', 'number_sub_type',  # number_idx is just the index value
                                    'unit_sub_type', 'unit_idx', 'unit_pattern',
                                    'end'],
                           index=numbers_idx)
    if len(numbers_idx) > 0:
        amounts.number_value = match_info.loc[numbers_idx, 'value'].values
        amounts.number_sub_type = match_info.loc[numbers_idx, 'sub_type'].values
        for i in numbers_idx:
            # get the number and the following two phrases (if they exist)
            next_two = match_info.loc[i:, :].head(3)
            # initialize the end location:
            amounts.loc[i, 'end'] = i
            if len(next_two) > 1:
                if conv_utils.df_get(next_two, 1, 'type') == 'spacer':
                    next_two = next_two.iloc[[0, 2], :]

                if conv_utils.df_get(next_two, 1, 'type') == 'unit':
                    amounts.loc[i, 'unit_pattern'] = next_two.pattern.iloc[1]
                    amounts.loc[i, 'unit_sub_type'] = next_two.sub_type.iloc[1]
                    amounts.loc[i, 'end'] = next_two.index[1]
                    amounts.loc[i, 'unit_idx'] = next_two.index[1]

    return amounts


def change_servings_line(line, convert_sisterless_numbers, multiplier):

    amounts = conv_utils.json_dict_to_df(line['amounts'])
    match_info = conv_utils.json_dict_to_df(line['match_info'])

    if len(amounts) > 0:

        side_by_side_idx = conv_utils.locate_amt_plus_amt_amounts(amounts=amounts, match_info=match_info)
        # now, merge any amounts that are meant to be together:
        for left_idx, right_idx, plus_idx in side_by_side_idx:
            match_info, amounts = conv_utils.combine_two_amounts_rows(left_idx=left_idx, right_idx=right_idx,
                                                                      plus_idx=plus_idx, amounts=amounts,
                                                                      match_info=match_info)

        for aidx in amounts.index:
            amount = amounts.loc[aidx, :]
            # is the number type and the unit type multipliable?
            # if unit doesn't exist, True and None = None; False and none = False.
            both_multipliable = (multipliable.get(amount['number_sub_type']) is True) and \
                                (multipliable.get(amount['unit_sub_type']) is True)
            # is the number alone but multipliable?
            sisterless_number = (not isinstance(amount.get('unit_pattern'), str)) and \
                                convert_sisterless_numbers and \
                                (multipliable.get(amount['number_sub_type']) is True)

            # if unit and number are multipliable, or sisterless numbers are OK:
            if both_multipliable or sisterless_number:
                amount = conv_utils.multiply_amount(amount, convert_to=None, multiplier=multiplier)
                if not sisterless_number:
                    if not isinstance(amount.number_value, str):
                        # this function says: given the new amount value given to us by the use of
                        # multiply_amount() above, now see if units should be converted up or downwards.
                        # If they do need to be converted; do that
                        amount = conv_utils.convert_amount_to_appropriate_unit(amount=amount)
                        # now, after that, see if the new amounts number is a decimal. If it is, does that
                        # decimal cross the threshold to be converted into a lower unit? (e.g. tbsp --> tsp?)
                        # If it does, change the match_info data frame
                        # by inserting four new rows (' |plus|fraction| ') into match_info. Also augment the
                        # amount row to show that it is a 'plus' amount.
                        match_info, amounts, amount = conv_utils.insert_rows_if_amount_decimal_crosses_threshold(
                            amount=amount,
                            amounts=amounts,
                            match_info=match_info
                        )
                amounts.loc[amount.name, :] = amount

        # now the multiplication has happened, giv em' some aftercare :P
        for aidx in amounts.index:
            amount = amounts.loc[aidx, :]
            match_info.loc[amount.name, 'name'] = conv_utils.multiply_number_to_str(number_val=amount.number_value,
                                                                                    multiplier=1.)
            match_info.loc[amount.name, 'value'] = amount.number_value

    # optional...
    amounts = amounts.sort_index()
    match_info = match_info.sort_index()

    match_info = conv_utils.update_plurality(match_info, amounts)
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

    # sort the data frame:
    match_info = match_info.sort_index(axis=0)

    amounts = get_amounts(match_info)
    match_info = conv_utils.update_plurality(match_info, amounts)

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
