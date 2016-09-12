# coding=utf8
import re
import pandas as pd
from .base_conversion_dicts import name_maps_numbers, name_maps_volume, name_maps_weight


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
    line = line.replace('.', '')
    # add whitespace padding:
    line = ' {} '.format(line)
    # remove double+ whitespaces:
    line = re.sub(' +', ' ', line)
    return line


def find_number_matches(line, name_maps):
    pattern = '|'.join(reversed(name_maps.index))
    # finds non-overlapping matches to our (sorted!) long joined pattern:
    matches = re.finditer(pattern, line)

    # base record data frame:
    out = pd.DataFrame(columns=['start', 'end', 'pattern', 'replacement', 'value'])
    for match in matches:
        start = match.start()
        end = match.end()
        # grab what actually caused the hit:
        pattern = line[start:end]
        # grab the relevant dict:
        replacement = ' {} '.format(name_maps.loc[pattern, 'name'])
        value = name_maps.loc[pattern, 'value']
        out.loc[len(out), :] = [start, end, pattern, replacement, value]

    return out


def parse_ingredient_line(line='2 and a half egg yolks, whisked'):

    original_line = line
    line = clean_line(line)
    matches = find_number_matches(line=line, name_maps=name_maps_numbers)
    # do the same for volume and units but determine plurality based on nearest number(s) to the left?

    line = multiple_replace(pattern_replace_dict={r.pattern: r.replacement for p, r in matches.iterrows()},
                            text=line)
    line = re.sub('^ | $', '', line)

    return dict(original_line=original_line,
                parsed_line=line,
                matches=matches)





