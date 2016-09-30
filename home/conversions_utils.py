# coding=utf8
from __future__ import generators, unicode_literals
import pandas as pd
import re
import numpy as np
from .unit_name_maps import multipliable, name_maps_fractions
from .utils import which_min
from .unit_conversion_matrices import CONVERSION_FACTORS


def change_servings(match_info, amounts, convert_sisterless_numbers, servings0, servings1):

    multiplier = float(servings1) / float(servings0)
    if multiplier == 1.:
        return match_info

    # now, merge any amounts that are meant to be together:
    side_by_side_idx = (amounts.start.iloc[1:]-1) == (amounts.end.iloc[:-1])
    side_by_side_idx = reversed(side_by_side_idx.index[side_by_side_idx].values)
    for i in side_by_side_idx:
        if match_info['sub_type'].iloc[i-1] == 'plus':
            i_pre = amounts.index[amounts.index.get_loc(i)-1]
            to_merge = amounts.loc[[i_pre, i], :]
            new_row = to_merge.iloc[0, :]
            new_row.end = to_merge.end.iloc[1]
            new_row.plus_name = match_info['name'].iloc[i-1]
            conversion_float = CONVERSION_FACTORS.conversions[to_merge.unit_name.iloc[1]][new_row.unit_name]
            new_row.number_value += to_merge.number_value.iloc[1]*conversion_float
            replace_rows(amounts, idx=[i_pre, i], new_row=new_row, by_iloc=False)

            # now, multiply values by appropriate servings *
            # then, if value unit crosses threshold, create multi_unit or different unit amount name
            # then, replace unit names with their singular or plural names based on new number value

            # BUT... we want to be able to handle plurality WITHOUT doing all this conversion stuff.
            # conversion stuff should only be required if servings are being changed.
            # ERGO....
            # This function should stop above, at around 410, and update unit names.
            # Then create function to create text from amounts and match_info data frames.
            # THEN if servings are changed, merge appropirate amounts and update the number values.

    for amount in amounts.iterrows():
        both_multipliable = multipliable[amount['number_sub_type']] and multipliable[amount['unit_sub_type']]
        sisterless_number = amount.get('unit') == np.nan and not convert_sisterless_numbers
        if both_multipliable or sisterless_number:
            amount.number_name = multiply_number(number_val=amount.number_value,
                                                 sub_type=amount.number_sub_type,
                                                 multiplier=multiplier)
            amount.number_value *= multiplier

    return amount


def df_get(df, iloc, col):
    try:
        x = df.iloc[iloc][col]
        return x
    except IndexError or KeyError:
        return None


def find_sequence(match_info, n, columns, patterns):
    i = n - 1
    n_patterns = len(patterns)
    # need to search backwards so that when rows are replaced, they are replaced back to front
    # and don't mess up the iloc match placements.
    while (i - n_patterns + 1) >= 0:
        comparison = [match_info[columns[j]].iloc[i - n_patterns + 1 + j] for j in range(n_patterns)]
        if patterns == comparison:
            match = i - n_patterns + 1
            i -= n_patterns
            yield range(match, match + n_patterns)
        else:
            i -= 1


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


def replace_rows(match_info, idx, new_row, by_iloc=True):
    if by_iloc:
        match_info = match_info.drop(match_info.index[idx])
    else:
        match_info = match_info.drop(idx)
    match_info = match_info.append(new_row)
    match_info = match_info.sort_index()

    return match_info


def replace_match_rows_with_aggregate(match_info, hits_gen, type, sub_type,
                                      value_func=lambda val0, val2: '{} {}'.format(val0, val2)):
    for i in hits_gen:
        idx = [i, i + 1, i + 2]
        rows = match_info.iloc[idx, :]
        start = int(rows.end.iloc[0])
        # print('--------------------------')
        # print(sub_type)
        # print(rows)
        new_row = pd.DataFrame(dict(start=start,
                                    end=rows.end.iloc[len(rows) - 1],
                                    name=''.join(rows.name),
                                    original=''.join(rows.original),
                                    value=value_func(rows.value.iloc[0], rows.value.iloc[2]),
                                    type=type, sub_type=sub_type, sister_idx=rows.sister_idx.iloc[2]),
                               index=[start])

        # first one shouldn't be neccessary:
        match_info.loc[match_info.sister_idx == match_info.index[i], 'sister_idx'] = start
        match_info.loc[match_info.sister_idx == match_info.index[i+1], 'sister_idx'] = start
        match_info.loc[match_info.sister_idx == match_info.index[i+2], 'sister_idx'] = start

        match_info = replace_rows(match_info=match_info, idx=idx, new_row=new_row)

    return match_info


def find_type_pattern(match_info, n, columns, patterns, middle_name_matches=None, middle_i_subtract=1):
    i = n-1
    n_patterns = len(patterns)
    # need to search backwards so that when rows are replaced, they are replaced back to front
    # and don't mess up the iloc match placements.
    while (i - n_patterns + 1) >= 0:
        comparison = [match_info[columns[j]].iloc[i - n_patterns + 1 + j] for j in range(n_patterns)]
        if patterns == comparison:
            if middle_name_matches is not None:
                if not match_info.iloc[i - middle_i_subtract]['name'] in middle_name_matches:
                    i -= 1
                    continue

            match = i-n_patterns+1
            i -= n_patterns
            yield match
        else:
            i -= 1


def number_to_string(value):

    if value % 1 == 0:
        string = str(int(value))
    else:
        fractions = name_maps_fractions.tail(10)
        integer = int(value)
        floater = value % 1
        fraction = fractions.name.iloc[which_min((fractions.value-floater).abs())]
        if integer == 0:
            string = str(fraction)
        else:
            string = '{}{}'.format(integer, fraction)

    return string


def multiply_number(sub_type, number_val, multiplier):

    if sub_type in ['range']:
        name = [number_to_string(float(v)*multiplier) for v in number_val.split(' ')]
        name = '{} to {}'.format(name[0], name[1])
    else:
        name = number_to_string(number_val*multiplier)

    # TODO improve this so that before number is converted into a string, its sister unit is checked.
    # TODO if the number is bigger than the sister unit's conversion limit, then convert into the sister unit's
    # TODO favorite sister (tsp --> tbsp) and re-name everything to say, e.g. '2 tablespoons and 1/2 teaspoons sugar'.
    # TODO ALSO - plurality needs to be dealt with when servings are changed.

    return name


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

