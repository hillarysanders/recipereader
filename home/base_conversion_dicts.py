# coding=utf8
from num2words import num2words

"""
Base conversion dictionaries that conversions.py will use to build nicely formatted conversion objects.
Not meant to be used directly.
"""

# name_maps_numbers = [
#     # don't want to match to... half and half, half chopped, etc
#     dict(pattern=['half', 'a half', 'one half', '1/2', '.5', 'halves', '½'],
#          name='½',
#          value=.5),
#     dict(pattern=['a quarter', 'one quarter', '1/4', '.25', 'a forth', 'quarters', '¼'],
#          name='¼',
#          value=.25),
#     dict(pattern=['a fifth', 'one fifth', '1/5', '.2', 'a fifth', 'fifths', '⅕'],
#          name='⅕',
#          value=.2),
#     dict(pattern=['one third', 'a third', '1/3', 'thirds', '⅓'],
#          name='⅓',
#          value=float(1) / 3),
#     dict(pattern=['one sixth', 'a sixth', '1/6', 'sixths', '⅙'],
#          name='⅙',
#          value=float(1) / 6),
#     dict(pattern=['one eighth', 'an eighth', '1/8', 'eighths', '⅛'],
#          name='⅛',
#          value=float(1) / 8),
#     dict(pattern=['the whole', 'a whole', 'one'],  # todo protect against e.g. 'one at at time'...
#          name='1',
#          value=1.)
# ]

name_maps_numbers = [
    # don't want to match to... half and half, half chopped, etc
    dict(pattern=['half', 'a half', 'one half', '1/2', '.5', 'halves'],
         name='1/2',
         value=.5),
    dict(pattern=['a quarter', 'one quarter', '1/4', '.25', 'a forth', 'quarters'],
         name='1/4',
         value=.25),
    dict(pattern=['a fifth', 'one fifth', '1/5', '.2', 'a fifth', 'fifths'],
         name='1/5',
         value=.2),
    dict(pattern=['one third', 'a third', '1/3', 'thirds'],
         name='1/3',
         value=float(1) / 3),
    dict(pattern=['one sixth', 'a sixth', '1/6', 'sixths'],
         name='1/6',
         value=float(1) / 6),
    dict(pattern=['one eighth', 'an eighth', '1/8', 'eighths'],
         name='1/8',
         value=float(1) / 8),
    dict(pattern=['the whole', 'a whole', 'one'],  # todo protect against e.g. 'one at at time'...
         name='1',
         value=1.)
]
# anything above 1 uses num_to_words
name_maps_volume = [
    dict(pattern=['teaspoon', 'tsp', 't'],
         singular='teaspoon',
         plural='tsp.'),
    dict(pattern=['tablespoon', 'tbsp', 'tbls', 'tbs', 'T'],
         singular='tablespoon',
         plural='tbsp.'),
    dict(pattern=['fluid ounce', 'fluid oz', 'ounce (fluid)', 'fl oz'],
         singular='fluid ounce',
         plural='fluid oz.'),
    dict(pattern=['cup'],
         singular='cup',
         plural='cups'),
    dict(pattern=['pint'],
         singular='pint',
         plural='pints'),  # technically pts. but nobody knows that
    dict(pattern=['quart'],
         singular='quart',
         plural='quarts'),
    dict(pattern=['gallon'],
         singular='gallon',
         plural='gallons'),
    dict(pattern=['liter', 'litre', 'ltr', 'lt', 'l'],
         singular='liter',
         plural='liters'),
    dict(pattern=['milliliter', 'millilitre', 'ml'],
         singular='milliliter',
         plural='ml')
]

name_maps_weight = [
    dict(pattern=['gr', 'g', 'grm', 'gram'],
         singular='gram',
         plural='grams'),
    dict(pattern=['kg', 'kilogram'],
         singular='kg',
         plural='kilograms'),
    dict(pattern=['milligram', 'mg'],
         singular='milligram',
         plural='mg'),
    dict(pattern=['lb', 'pound'],
         singular='lb.',
         plural='lbs.'),
    dict(pattern=['oz', 'ounce', 'onze', 'onza'],
         singular='ounce',
         plural='oz.')
]


def _prep_name_map(name_maps):
    """
    a name_map in this file is a list of dictionaries, where each
    dict shows a bunch of strings (names) that map to its 'true' (chosen) name.
    e.g. 'T.', 'tablespoon' will all map to 'tbsp.'.
    This function preps all the possible pattern strings by augmenting them
    via capitalization, etc. The transforms the dicts into a nicer to handle dataframe.
    """
    # capitalize stuff:
    name_maps = _extend_pattern_with_capitalization(name_maps)
    # add spaces:
    name_maps = _add_spaces_to_sides(name_maps)
    # coerce to dataframe:
    name_maps = pd.concat([pd.DataFrame(d) for d in name_maps])
    name_maps = name_maps.drop_duplicates('pattern')
    name_maps = name_maps.reset_index(drop=True)
    name_maps = name_maps.set_index('pattern')

    return name_maps


def _add_spaces_to_sides(name_maps):
    for i in range(len(name_maps)):
        name_maps[i]['pattern'] = [' {} '.format(n) for n in name_maps[i]['pattern']]
    return name_maps


def _extend_pattern_with_capitalization(name_maps):
    for d in name_maps:
        replacement = d['pattern']
        capitalized = [el.capitalize() for el in replacement if el != 't']
        upper = [el.upper() for el in replacement if el != 't']
        replacement.extend(capitalized)
        replacement.extend(upper)
        replacement = list(set(replacement))

    return name_maps


def _extend_number_name_maps(name_maps_numbers, n=1000):
    """
    Extends name_maps_numbers with maps from e.g. 'twenty four' to 24.
    :param name_maps_numbers:
    :param n:
    :return:
    """
    for i in range(2, n):
        el = dict(pattern=[num2words(i), str(i)], name=str(i), value=float(i))
        if (i % 12) == 0:
            # two dozen, etc...
            el['pattern'].extend(['{} dozen'.format(num2words(i/12))])

            if i == 12:
                # include 'a dozen'
                el['pattern'].extend(['a dozen'])

        name_maps_numbers.extend([el])

    return name_maps_numbers


# use num2words:
name_maps_numbers = _extend_number_name_maps(name_maps_numbers, n=100)
# capitalize stuff:
name_maps_numbers = _prep_name_map(name_maps_numbers)
name_maps_volume = _prep_name_map(name_maps_volume)
name_maps_weight = _prep_name_map(name_maps_weight)

