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


def clean_line(line):
    # remove periods:
    line = line.replace('. ', ' ')  # doesn't remove e.g. .25 or .5
    line = line.replace('-', ' ')  # doesn't remove e.g. .25 or .5
    # make uniform lines:
    line = line.replace('\r\n', '\n').replace('\r', '\n')
    # add whitespace padding:
    line = ' {} '.format(line)
    # replace () with placeholder:
    line = line.replace('(', ' _(_ ').replace(')', ' _)_ ')
    # # remove double+ whitespaces:
    # line = re.sub(' +', ' ', line)
    return line


def find_number_matches(line, name_maps):
    pat = '|'.join(reversed(name_maps.index))
    # finds non-overlapping matches to our (sorted!) long joined pattern:
    matches = re.finditer(pat, line)

    # base record data frame:
    out = pd.DataFrame(columns=['start', 'end', 'pattern', 'replacement', 'value'])
    for match in matches:
        start = match.start()
        end = match.end()
        # grab what actually caused the hit:
        pattern = line[start:end]
        # grab the relevant dict:
        replacement = ' {} '.format(name_maps.loc[pattern, 'name'])  # todo spaces on sides? But then e.g. '2 cups'?...
        value = name_maps.loc[pattern, 'value']
        out.loc[len(out), :] = [start, end, pattern, replacement, value]

    return out


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
    patterns = ['[ \(]{}s?[\) $]|^{} | {}$'.format(p,p,p) for p in name_maps.index]
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
            if re.search('[) ]$', p):
                p = p[:-1]
                end -= 1
            if re.search('^[( ]', p):
                p = p[1:]
                start += 1

            # todo raise warning if p is not in the index of name_maps
            pidx = p if p in name_maps.index else p[:-1]
            info = pd.DataFrame(name_maps.loc[pidx, :]).T
            info['original'] = p
            info['start'] = start + placement
            info['end'] = end + placement
            info['pattern'] = pidx

            # handle unit plurality
            if info.loc[pidx, 'type'] in ['volume', 'weight']:
                # was the last number != 1?
                is_plural = 'unknown'
                if len(match_info)>0:
                    if any(match_info.type == 'number'):
                        m = match_info.loc[match_info.type == 'number', 'value']
                        if len(m)>1:
                            m = m.values[-1]
                        if m == 1:
                            is_plural = False
                            info['value'] = info['singular']
                        else:
                            is_plural = True
                            info['value'] = info['plural']
                        info['is_plural'] = is_plural
                # if that didn't work:
                if is_plural not in [True, False]:
                    # todo raise warning that plurality could not be found...
                    info['value'] = info['original']

            placement = end
            match_info = pd.concat([match_info, info])
        else:
            end = len(line)

        line = line[end:]

    # todo now add rows for all the text in between the match starts and end, and then sort the dataframe by start! <3.
    # todo now add rows for all the text in between the match starts and end, and then sort the dataframe by start! <3.
    # todo now add rows for all the text in between the match starts and end, and then sort the dataframe by start! <3.
    # todo how to handle floats? Have to handle number parsing and periods somehow.... Maybe if type=='number' look to
    # todo    the left, if it's a period, then combine that and multiple value by .01. If not, then look to the right.
    # todo    If it's a period or dash and then a number, combine the two by addition....
    # todo    hm. OR. Add a '[0-9]*\.?[0-9]* type pattern to the start of the pattern above and just add a section
    # todo    that says, oh, this is a float and not in the index, so just do (float(trim(p)). Hm. That might be best.
    # todo    probably faster.

    return match_info


def parse_ingredients(x):
    x = clean_newlines(x)
    lines = x.split('\n')
    results_dict = {str(i): parse_ingredient_line(lines[i]) for i in range(len(lines))}
    return results_dict


def get_highlighted_ingredients(recipe, prefix='<highlighted>', postfix='</highlighted>'):
    ing = recipe.ingredients
    idx = sorted(ing.keys())
    highlighted = []
    for i in idx:
        line = ing[i]['parsed_line']
        x = parse_ingredient_line(line)
        matches = x['matches']

        positions = sorted([[m['start'], m['end']] for m in matches.values()])
        h = ''
        end_ = 0
        for se in positions:
            start = se[0]
            end = se[1]
            h += line[end_:start]+prefix
            h += line[start:end]+postfix
            end_ = end
        h += line[end:len(line)]
        highlighted.append(h)

        # todo!! highlights ARE working (yay!) but the placement is off because the match positions refer to the line
        # todo   with e.g. '_(_' instead of '(' values, etc. I think ideally we want the output dict to contain
        # todo   start and end values of the final line, not the 'orginal' (actually, the preformatted) original line.
        # Probably end up redesigning the match dict stored object a bit.

    return highlighted


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