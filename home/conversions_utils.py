# coding=utf8
from __future__ import generators, unicode_literals
import pandas as pd
import re
import numpy as np
from .unit_name_maps import multipliable, name_maps_fractions, name_maps
from .utils import which_min
from .unit_conversion_matrices import CONVERSION_FACTORS


def update_plurality(match_info, amounts, replace_name=True, only_change_multipliable=True):
    if len(amounts) > 0:
        for i in amounts.index[~amounts.isnull().unit_idx]:
            row = amounts.loc[i, :]
            if multipliable[row['unit_sub_type']] or not only_change_multipliable:
                unit_name = name_maps.loc[row.unit_pattern, 'singular']
                if unit_name != '':
                    if isinstance(row.number_value, str):
                        number_name = number_to_string(float(row.number_value.split(' ')[-1]))
                    else:
                        number_name = number_to_string(row.number_value)
                        if replace_name:
                            match_info.loc[row.name, 'name'] = number_name

                    column = get_plurality_from_string(number_name=number_name)
                    unit_name = name_maps.loc[row['unit_pattern'], column]
                    match_info.loc[row['unit_idx'], 'name'] = unit_name

    return match_info


def number_to_string(value):

    if np.abs(np.abs((value % 1) - .5) - .5) < .05:
        string = str(int(np.round(value)))
    else:
        fractions = name_maps_fractions.tail(10)
        integer = int(value)
        floater = value % 1
        fraction = fractions.name.iloc[which_min((fractions.value - floater).abs())]
        if integer == 0:
            string = str(fraction)
        else:
            string = '{}{}'.format(integer, fraction)

    return string


def get_plurality_from_string(number_name):
    # a number is singular if it is 1, or is a fraction whose numerator is one.
    # therefore:
    if re.match('^(one|a |1/|⅛|⅙|⅓|⅕|¼|½|1$)', number_name, flags=re.IGNORECASE):
        # note that this won't match to 1 1/2 cups, which is good.
        return 'singular'
    else:
        return 'plural'


def multiply_number_to_str(number_val, multiplier=1.):
    if isinstance(number_val, str):
        name = [number_to_string(float(v) * multiplier) for v in number_val.split(' ')]
        name = '{} to {}'.format(name[0], name[1])
    else:
        name = number_to_string(number_val * multiplier)

    # TODO improve this so that before number is converted into a string, its sister unit is checked.
    # TODO if the number is bigger than the sister unit's conversion limit, then convert into the sister unit's
    # TODO favorite sister (tsp --> tbsp) and re-name everything to say, e.g. '2 tablespoons and 1/2 teaspoons sugar'.
    # TODO ALSO - plurality needs to be dealt with when servings are changed.

    return name


def multiply_amount(amount, convert_to=None, multiplier=None):

    if multiplier is None and convert_to is not None:
        unit_name = name_maps['singular'].get(str(amount.unit_pattern))
        if unit_name is None:
            # todo I think this should be != '' not 'not None'
            unit_name = 'pcs'
        multiplier = CONVERSION_FACTORS.conversions[unit_name][convert_to]
        amount.unit_pattern = convert_to
        # amount.unit_name = unit_name
    elif convert_to is None and multiplier is not None:
        # just changing servings, not units:
        pass
    else:
        print('PROBLEM: Exactly 1 of the two (convert_to and multiplier) arguments should be None.')
        return amount

    if isinstance(amount.number_value, str):
        split = amount.number_value.split(' ')
        amount.number_value = ' '.join([str(float(n) * multiplier) for n in split])
    else:
        amount.number_value *= multiplier

    return amount


def get_number_value_avg(amount):
    if isinstance(amount.number_value, str):
        number_value = np.mean([float(v) for v in amount.number_value.split(' ')])
    else:
        number_value = amount.number_value

    return number_value


def convert_amount_to_appropriate_unit(amount):
    """
    # if value is below unit's threshold, convert to that unit.
    # if value is above unit's threshold, convert to that unit.
    """
    unit_name = name_maps.loc[amount.unit_pattern, 'singular']
    unit_thresholds = CONVERSION_FACTORS.thresholds.get(unit_name)
    number_value = get_number_value_avg(amount)

    if unit_thresholds is not None:
        if number_value < unit_thresholds['min']:
            convert_to = unit_thresholds['smaller_unit']
            amount = multiply_amount(amount=amount, convert_to=convert_to, multiplier=None)
        elif number_value >= unit_thresholds['max']:
            convert_to = unit_thresholds['larger_unit']
            amount = multiply_amount(amount=amount, convert_to=convert_to, multiplier=None)

    return amount


def insert_rows_if_amount_decimal_crosses_threshold(amount, amounts, match_info, round=8):
    """
    This function takes an amounts value's decimal (that has just been multiplied, presumably),
    and creates extra match_info rows if needed, as determined by the amount unit's conversion thresholds.
    Generally to be used in combination (after) convert_amount_to_appropriate_unit().
    :param amount:
    :param match_info:
    :return:
    """
    # now, if decimal is below threshold, create a secondary amount:
    decimal = amount.number_value % 1
    unit_name = name_maps.loc[amount.unit_pattern, 'singular']
    unit_thresholds = CONVERSION_FACTORS.thresholds.get(unit_name)
    if unit_thresholds is not None:
        if 0 < decimal < unit_thresholds['min']:
            if not unit_thresholds['decimals_ok'] or amount.number_value < 1:
                convert_to = unit_thresholds['smaller_unit']
                dec_multiplier = CONVERSION_FACTORS.conversions[unit_name][convert_to]
                add_number_name = multiply_number_to_str(number_val=decimal,
                                                         multiplier=dec_multiplier)
                # todo don't think this line is needed:
                add_unit_name = name_maps.loc[convert_to, get_plurality_from_string(add_number_name)]

                # the new index will be a little past the start of the second to last phrase, since
                # with characters, start and end indices overlap (so we don't want the start of the insert
                # to go over the end of the last phrase, since that will also cause the insert to go over the beginning
                # of the next. Also could just do minus.
                add_on_start_end = float(match_info.loc[amount.name:amount.end, 'end'].tail(2).iloc[0])
                new_dec_number = np.round(dec_multiplier * decimal, round)
                mi_row = pd.DataFrame(dict(pattern=[np.nan, np.nan, np.nan, convert_to],
                                           # start=add_on_start_end, end=add_on_start_end,
                                           type=['text', 'number', 'spacer', 'unit'],
                                           sub_type=['plus', amount.number_sub_type,
                                                     np.nan, amount.unit_sub_type],
                                           value=[np.nan, new_dec_number, np.nan, np.nan],
                                           original='',
                                           name=[' plus ', add_number_name, ' ', add_unit_name]),
                                      index=[add_on_start_end + .01, add_on_start_end + .02,
                                             add_on_start_end + .03, add_on_start_end + .04])

                # modify the amounts  dataframe so it contains two amounts, now:
                amount_new_row = pd.DataFrame(dict(number_value=new_dec_number,
                                                   number_sub_type='fraction',
                                                   unit_sub_type=amount.unit_sub_type,
                                                   unit_idx=add_on_start_end + .04,
                                                   end=add_on_start_end + .04,
                                                   unit_pattern=convert_to), index=[add_on_start_end + .02])

                # modify the original amount row so that it's just an int now:
                amount.number_value = int(amount.number_value)

                # final prep:
                match_info = match_info.append(mi_row)
                amounts = amounts.append(amount_new_row)

    return match_info, amounts, amount


def combine_two_amounts_rows(left_idx, right_idx, plus_idx, amounts, match_info):
    to_merge = amounts.loc[[left_idx, right_idx], :]
    new_row = to_merge.iloc[0, :]
    # new_row.plus_idx = plus_idx
    unit_name_1 = name_maps.loc[to_merge.unit_pattern.iloc[1], 'singular']
    unit_name_2 = name_maps.loc[new_row.unit_pattern, 'singular']
    conversion_float = CONVERSION_FACTORS.conversions[unit_name_1][unit_name_2]
    new_row['number_value'] += to_merge.number_value.iloc[1] * conversion_float
    new_row['end'] = to_merge.end.iloc[1]
    amounts = replace_rows(amounts, idx=[left_idx, right_idx], new_row=new_row, by_iloc=False)

    match_info_rows_to_drop = match_info.loc[plus_idx:to_merge.end.iloc[1], :].index
    match_info = match_info.drop(match_info_rows_to_drop)

    return match_info, amounts


def json_dict_to_df(df):
    amounts = pd.DataFrame.from_dict(df, orient='index')
    amounts.index = [float(i) for i in amounts.index]
    amounts = amounts.sort_index(axis=0)
    amounts = amounts.replace('', value=np.nan)
    return amounts


def df_to_json_ready_dict(df):
    df = df.sort_index(axis=0)
    df.index = [str(i) for i in df.index]

    df = df.fillna('').to_dict(orient='index')
    return df


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


def lookback_for_type_from_pattern(match_info, regex_pattern, lookback_type, new_sub_type, lookback=3,
                                   dont_skip_over_type='text'):
    lookback += 1

    if any(match_info.index.duplicated()):
        print('WARNING: DUPLICATED INDEX VALUES in match_info.')
    idx = [i for i in match_info.index if re.match(regex_pattern, match_info.loc[i, 'name'])]
    for i in idx:
        m = match_info.loc[:i, :].tail(lookback)

        # cut off anything before a unit, though:
        unit_location = m.loc[m.type == dont_skip_over_type].index.max()
        if isinstance(unit_location, int):
            m = m.iloc[m.index.get_loc(unit_location):, :]

        is_number = m.type == lookback_type
        if any(is_number):
            hit = m.loc[is_number]
            hit = hit.index[-1]
            match_info.loc[hit, 'sub_type'] = new_sub_type

    return match_info


def lookforward_for_type_from_pattern(match_info, regex_pattern, hit_type, new_sub_type, lookforward=1):
    lookforward += 1
    idx = [i for i in match_info.index if re.search(regex_pattern, match_info.loc[i, 'name'])]
    for i in idx:
        m = match_info.loc[i:, :].head(lookforward)
        is_number = m.type == hit_type
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

        # first one shouldn't be necessary:
        match_info.loc[match_info.sister_idx == match_info.index[i], 'sister_idx'] = start
        match_info.loc[match_info.sister_idx == match_info.index[i + 1], 'sister_idx'] = start
        match_info.loc[match_info.sister_idx == match_info.index[i + 2], 'sister_idx'] = start

        match_info = replace_rows(match_info=match_info, idx=idx, new_row=new_row)

    return match_info


def find_type_pattern(match_info, n, columns, patterns, middle_name_matches=None, middle_i_subtract=1):
    i = n - 1
    n_patterns = len(patterns)
    # print('columns: {}'.format(columns))
    # print('n: {}'.format(n))

    # need to search backwards so that when rows are replaced, they are replaced back to front
    # and don't mess up the iloc match placements.
    while (i - n_patterns + 1) >= 0:
        comparison = [match_info[columns[j]].iloc[i - n_patterns + 1 + j] for j in range(n_patterns)]
        if patterns == comparison:
            if middle_name_matches is not None:
                if not match_info.iloc[i - middle_i_subtract]['name'] in middle_name_matches:
                    i -= 1
                    continue

            match = i - n_patterns + 1
            i -= n_patterns
            # print('Match!')
            # print('i={}, patterns={}, match={}'.format(i, patterns, match))
            yield match
        else:
            # print('No match.')
            i -= 1


def insert_text_match_info_rows(match_info, original_line):
    nrows = len(match_info)
    nchars = len(original_line)
    if nrows == 0:
        match_info = pd.DataFrame(dict(type='text', name=original_line, original=original_line,
                                       start=0, end=nchars, sub_type='', sister_idx=None),
                                  index=[0.])
    else:
        for i in range(nrows + 1):
            if i == 0:
                # look to the beginning of the line to the start of the first pattern (this pattern)
                start = 0
                end = match_info.iloc[i].start
            elif i >= nrows:
                # look to the last of the last pattern to the end of the line
                start = match_info.iloc[i - 1]['end']
                end = nchars
            else:
                # look to the end of the last pattern to the start of this pattern
                start = match_info.iloc[i - 1]['end']
                end = match_info.iloc[i].start

            if end > start:
                text = original_line[start:end]
                newrow = pd.DataFrame(dict(type='text', name=text, original=text, start=start, end=end,
                                           sub_type='', sister_idx=None),
                                      index=[float(start)])
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
    match_dict = match_dict.fillna('')
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
        match_dicts = parsed_text[i]['match_info']
        if not isinstance(match_dicts, pd.DataFrame):
            match_dicts = json_dict_to_df(match_dicts)

        text = ''.join(_add_highlight(match_dicts.iloc[k, :],
                                      type_or_sub_types=type_or_sub_types) for k in range(len(match_dicts)))
        highlighted.append(text)

    return highlighted


def locate_amt_plus_amt_amounts(amounts, match_info):
    """
    finds amounts rows that are side by side and separated by 'plus' subtype phrases
    in match_info. yields indices of the two amounts rows.
    generator
    note that it searches in reverse so row merges don't mess things up...
    """
    amt_index = amounts.index[::-1]
    for left, right in zip(amt_index[1:], amt_index):
        left_end = match_info.index.get_loc(amounts.loc[left, 'end'], method='pad')
        if len(match_info) > (left_end + 2):
            # we are searching for amount PLUS amount, so left end + 2 = right start
            expected_start = match_info.index[left_end + 2]
            if expected_start == right:
                plus_idx = match_info.index[left_end + 1]
                if match_info.sub_type[plus_idx] == 'plus':
                    # yield index of the two amounts rows to be joined:
                    yield (left, right, plus_idx)


def merge_amounts_meant_to_be_together(amounts, match_info):
    if len(amounts) > 0:
        # now, merge any amounts that are meant to be together:
        side_by_side_idx = locate_amt_plus_amt_amounts(amounts=amounts, match_info=match_info)
        for left_idx, right_idx, plus_idx in side_by_side_idx:
            match_info, amounts = combine_two_amounts_rows(left_idx=left_idx, right_idx=right_idx,
                                                           plus_idx=plus_idx, amounts=amounts,
                                                           match_info=match_info)

    return amounts, match_info


def highlight_changed_amounts(parsed_text, convert_sisterless_numbers=True, ingredients=False):
    """
    :param parsed_text: output of parse_ingredients()
    """
    idx = sort_char_keys(parsed_text)
    highlighted = []
    for i in idx:
        match_info = parsed_text[i]['match_info']
        amounts = parsed_text[i]['amounts']

        if not isinstance(match_info, pd.DataFrame):
            match_info = json_dict_to_df(match_info)
        if not isinstance(amounts, pd.DataFrame):
            amounts = json_dict_to_df(amounts)

        # merging amounts so that e.g. '1 tablespoon plus 1 teaspoon' is highlighted as a single amount.
        amounts, _match_info = merge_amounts_meant_to_be_together(amounts, match_info)

        match_info = match_info.fillna('')
        for aidx in amounts.index:
            amount = amounts.loc[aidx, :]
            # is the number type (and the unit type, if it exists) multipliable?
            is_multipliable = is_amount_multipliable(amount,
                                                     convert_sisterless_numbers=convert_sisterless_numbers)

            if is_multipliable:
                match_info.loc[aidx, 'name'] = '<multiplied_amount>{}'.format(match_info.loc[aidx, 'name'])
                end_idx = match_info.index.get_loc(amount.end, method='pad')
                match_info['name'].iloc[end_idx] += '</multiplied_amount>'

        text = ''.join(match_info.name)
        if ingredients:
            text = '<text_indent>{}</text_indent>'.format(text)
        highlighted.append(text)

    highlighted = '<br>'.join(highlighted)

    return highlighted


def is_amount_multipliable(amount, convert_sisterless_numbers=True):

    # initialize:
    is_multipliable = False
    # first off, are both the unit sub_type and number sub_type multipliable?
    both_multipliable = (multipliable.get(amount['number_sub_type']) is True) and \
                        (multipliable.get(amount['unit_sub_type']) is True)
    if both_multipliable:
        is_multipliable = True
    else:
        if convert_sisterless_numbers:
            # is the number alone but multipliable?
            sisterless_number = (not isinstance(amount.get('unit_pattern'), str)) and \
                                (multipliable.get(amount['number_sub_type']) is True)
            if sisterless_number:
                is_multipliable = True

    return is_multipliable