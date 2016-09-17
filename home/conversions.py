# coding=utf8
from __future__ import unicode_literals
import re
import pandas as pd
from .base_conversion_dicts import name_maps_numbers, name_maps_volume, name_maps_weight, name_maps


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


def parse_ingredient_line(line):
    # todo add in patterns and treatment for floats, e.g. 2.5 pounds.
    # todo change number treatment entirely so that it can appear next to words. e.g. 30g.
    # sooo... first look for numbers. Then loop through the rest of the text using this code?
    patterns = ['[ \(]{}s?[\) $]|^{} | {}$'.format(p, p, p) for p in name_maps.index]
    pattern = '|'.join(reversed(patterns))
    # pattern = re.compile(pattern)

    original_line = line
    match_info = pd.DataFrame()
    placement = 0
    while len(line) > 0:
        match = re.search(pattern=pattern, string=line)
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

            # if p isn't in the index of name_maps, it probably has an s on the end:
            pidx = p if p in name_maps.index else p[:-1]
            # we want the start and end to stay the same but the pattern to forget the s.
            # todo raise warning if p is still not in the index of name_maps

            info = pd.DataFrame(name_maps.loc[pidx, :]).T
            info['original'] = p
            info['start'] = start + placement
            info['end'] = end + placement
            info['pattern'] = pidx

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

            placement = info.loc[:, 'end'][0]
            match_info = pd.concat([match_info, info])
        else:
            end = len(line)

        line = line[end:]

    nrows = len(match_info)
    nchars = len(original_line)
    if nrows == 0:
        match_info = pd.DataFrame(dict(type='text', name=original_line, original=original_line,
                                       start=0, end=nchars), index=['text'])
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
                    newrow = pd.DataFrame(dict(type='text', name=text, original=text, start=start, end=end),
                                          index=['text'])
                    match_info = pd.concat([match_info, newrow])
                elif end < start:
                    raise Warning('End < start??? Indexing got messed up...')

    print(match_info)
    print('N ROWS: {}'.format(nrows))
    print(original_line)
    print('RANGE: {}'.format(range(nrows+1)))
    match_info = match_info.sort_values(by='start')
    match_info.index = [str(i) for i in match_info.start.values]
    print(''.join(match_info.name))
    # todo how to handle floats? Have to handle number parsing and periods somehow.... Maybe if type=='number' look to
    # todo    the left, if it's a period, then combine that and multiple value by .01. If not, then look to the right.
    # todo    If it's a period or dash and then a number, combine the two by addition....
    # todo    hm. OR. Add a '[0-9]*\.?[0-9]* type pattern to the start of the pattern above and just add a section
    # todo    that says, oh, this is a float and not in the index, so just do (float(trim(p)). Hm. That might be best.
    # todo    probably faster. Include word-numbers ('two') in this above code, just do a pre-search for numeric values,
    # todo    since you can have e.g. "30g." "4lb" phrases all the time.

    return match_info.fillna('').to_dict(orient='index')


def parse_ingredients(x):
    x = clean_newlines(x)
    lines = x.split('\n')
    results_dict = {str(i): parse_ingredient_line(lines[i]) for i in range(len(lines))}
    return results_dict


def _add_highlight(match_dict, prefix='<highlighted>', postfix='</highlighted>'):
    if match_dict['type'] == 'text':
        txt = match_dict['name']
    else:
        txt = '{}{}{}'.format(prefix, match_dict['name'], postfix)

    return txt


def sort_char_keys(d):
    return list(map(str, sorted(map(int, d.keys()))))


def get_highlighted_ingredients(recipe):
    ing = recipe.ingredients
    idx = sort_char_keys(ing)
    highlighted = []
    for i in idx:
        match_dicts = ing[i]
        text = ''.join(_add_highlight(match_dicts[k]) for k in sort_char_keys(match_dicts))
        highlighted.append(text)

    print(idx)
    print(highlighted)
    print(pd.DataFrame(ing['0']))
    print('_______________________')
    return highlighted

#
# def find_number_matches(line, name_maps):
#     pat = '|'.join(reversed(name_maps.index))
#     # finds non-overlapping matches to our (sorted!) long joined pattern:
#     matches = re.finditer(pat, line)
#
#     # base record data frame:
#     out = pd.DataFrame(columns=['start', 'end', 'pattern', 'replacement', 'value'])
#     for match in matches:
#         start = match.start()
#         end = match.end()
#         # grab what actually caused the hit:
#         pattern = line[start:end]
#         # grab the relevant dict:
#         replacement = ' {} '.format(name_maps.loc[pattern, 'name'])  # todo spaces on sides? But then e.g. '2 cups'?...
#         value = name_maps.loc[pattern, 'value']
#         out.loc[len(out), :] = [start, end, pattern, replacement, value]
#
#     return out
#
#
# def clean_line(line):
#     # remove periods:
#     line = line.replace('. ', ' ')  # doesn't remove e.g. .25 or .5
#     line = line.replace('-', ' ')  # doesn't remove e.g. .25 or .5
#     # make uniform lines:
#     line = line.replace('\r\n', '\n').replace('\r', '\n')
#     # add whitespace padding:
#     line = ' {} '.format(line)
#     # replace () with placeholder:
#     line = line.replace('(', ' _(_ ').replace(')', ' _)_ ')
#     # # remove double+ whitespaces:
#     # line = re.sub(' +', ' ', line)
#     return line
#
#
# def parse_ingredient_line(line='2 and a half egg yolks, whisked'):
#
#     original_line = line
#     line = clean_line(line)
#     matches = find_number_matches(line=line, name_maps=name_maps_numbers)
#     # do the same for volume and units but determine plurality based on nearest number(s) to the left?
#
#     if len(matches) > 0:
#         line = multiple_replace(pattern_replace_dict={r.pattern: r.replacement for
#                                                       p, r in matches.iterrows()},
#                                 text=line)
#
#     line = line.replace(' _(_ ', '(').replace(' _)_ ', ')')
#     line = re.sub('^ | $', '', line)
#
#     # coerce matches df to dict:
#     matches.index = [str(i) for i in matches.index]
#     matches = matches.to_dict(orient='index')
#
#     return dict(original_line=original_line,
#                 parsed_line=line,
#                 matches=matches)
#
#
# def parse_ingredients(lines):
#     ll = lines.split('\n')
#     results_dict = {str(i): parse_ingredient_line(ll[i]) for i in range(len(ll))}
#     return results_dict