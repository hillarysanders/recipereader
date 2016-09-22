# coding=utf8
from __future__ import unicode_literals
from num2words import num2words
import pandas as pd
"""
Base conversion dictionaries that conversions.py will use to build nicely formatted conversion objects.
Not meant to be used directly.
"""

name_maps_fractions = [
    # don't want to match to... half and half, half chopped, etc
    dict(pattern=['half', 'a half', 'one half', '1/2', '\.5', 'halves', '½'],
         name='½',
         value=.5),
    dict(pattern=['a quarter', 'one quarter', '1/4', '\.25', 'a forth', 'quarters', '¼'],
         name='¼',
         value=.25),
    dict(pattern=['a fifth', 'one fifth', '1/5', '\.2', 'a fifth', 'fifths', '⅕'],
         name='⅕',
         value=.2),
    dict(pattern=['one third', 'a third', '1/3', 'thirds', '⅓'],
         name='⅓',
         value=float(1) / 3),
    dict(pattern=['one sixth', 'a sixth', '1/6', 'sixths', '⅙'],
         name='⅙',
         value=float(1) / 6),
    dict(pattern=['one eighth', 'an eighth', '1/8', 'eighths', '⅛'],
         name='⅛',
         value=float(1) / 8)
    # dict(pattern=['the whole', 'a whole', 'one'],  # todo protect against e.g. 'one at at time'...
    #      name='1',
    #      value=1.)
]

# anything above 1 uses num_to_words
name_maps_volume = [
    dict(pattern=['teaspoon', 'tsp', 't', 'teaspoons', 't\.', 'tsp\.'],
         singular='teaspoon',
         plural='teaspoons'),
    dict(pattern=['tablespoon', 'tablespoons', 'tbsp', 'tbls', 'tbs', 'T', 'tbsp\.', 'tbls\.', 'tbs\.', 'T\.'],
         singular='tablespoon',
         plural='tablespoons'),
    dict(pattern=['fluid ounce', 'fluid ounces', 'fluid oz', 'ounces (fluid)', 'ounce (fluid)' 'fl oz', 'fl oz\.',
                  'fluid oz\.', 'oz (fluid)', 'oz\. (fluid)'],
         singular='fluid ounce',
         plural='fluid oz.'),
    dict(pattern=['cup', 'cups'],
         singular='cup',
         plural='cups'),
    dict(pattern=['pint', 'pints', 'pts', 'pts\.', 'pt', 'pt\.'],
         singular='pint',
         plural='pints'),  # technically pts. but nobody knows that
    dict(pattern=['quart', 'quarts', 'qrt\.', 'qt\.', 'qrt', 'qt'],
         singular='quart',
         plural='quarts'),
    dict(pattern=['gallon', 'gallons', 'gal\.', 'gal'],  # gal?
         singular='gallon',
         plural='gallons'),
    dict(pattern=['liter', 'liters', 'litres', 'litre', 'ltr', 'lt', 'l', 'l\.', 'lt\.', 'ltr\.'],
         singular='liter',
         plural='liters'),
    dict(pattern=['milliliter', 'milliliters', 'millilitre', 'millilitres', 'ml', 'ml\.'],
         singular='milliliter',
         plural='ml')
]

name_maps_weight = [
    dict(pattern=['gr', 'g', 'grm', 'gram', 'grams', 'g\.', 'gr\.'],
         singular='gram',
         plural='grams'),
    dict(pattern=['kg', 'kilogram', 'kilograms', 'kg\.'],
         singular='kg',
         plural='kilograms'),
    dict(pattern=['milligram', 'mg', 'milligram', 'mg\.'],
         singular='milligram',
         plural='mg'),
    dict(pattern=['lb', 'pound', 'lbs', 'pounds', 'lb\.', 'lbs\.'],
         singular='lb.',
         plural='lbs.'),
    dict(pattern=['oz', 'ounce', 'onze', 'onza', 'oz\.'],
         singular='ounce',
         plural='oz.')
]

# NOT ACTUALLY A WEIGHT:
pcs = dict(pattern=['pcs', 'pieces', 'piece', 'dashes', 'dash', 'handfuls', 'handful', 'scoop', 'scoops', 'package',
                    'package', 'packages', 'bag', 'bags', 'bottle', 'bottles', 'sack', 'sacks',
                    'box', 'boxes', 'container', 'containers', 'can', 'cans', 'unit', 'units',
                    'handful', 'handfuls', 'slice', 'slices'],
           type='unit',
           sub_type='pcs')
pcs['name'] = pcs['pattern']


# line = '2 cups (12-oz. pkg.) chocolate chips'


def _prep_name_map(name_maps):
    """
    a name_map in this file is a list of dictionaries, where each
    dict shows a bunch of strings (names) that map to its 'true' (chosen) name.
    e.g. 'T.', 'tablespoon' will all map to 'tbsp.'.
    This function preps all the possible pattern strings by augmenting them
    via capitalization, etc. The transforms the dicts into a nicer to handle dataframe.
    """
    # # capitalize stuff:
    # name_maps = _extend_pattern_with_capitalization(name_maps)
    # # add spaces:
    # name_maps = _add_spaces_to_sides(name_maps)
    # coerce to dataframe:
    name_maps = pd.concat([pd.DataFrame(d) for d in name_maps])
    name_maps = name_maps.drop_duplicates('pattern')

    # sort by pattern length:
    name_maps['pattern_length'] = [len(p) for p in name_maps.pattern]
    name_maps = name_maps.sort_values(by=['pattern_length'])
    del name_maps['pattern_length']

    name_maps = name_maps.reset_index(drop=True)
    name_maps = name_maps.set_index('pattern')

    return name_maps


def _get_name_maps_english_numbers(n=1000):
    """
    e.g. 'twenty four' = 24.
    :param n:
    :return:
    """
    name_maps_english_num = []
    for i in range(2, n):
        el = dict(pattern=[num2words(i)], name=str(i), value=float(i))
        if (i % 12) == 0:
            # two dozen, etc...
            el['pattern'].extend(['{} dozen'.format(num2words(i/12))])

            if i == 12:
                # include 'a dozen'
                el['pattern'].extend(['a dozen'])

        name_maps_english_num.extend([el])

    return name_maps_english_num


# use num2words:
name_maps_english_numbers = _get_name_maps_english_numbers(n=100)
# manicure stuff:
name_maps_english_numbers = _prep_name_map(name_maps_english_numbers)
name_maps_english_numbers['type'] = 'number'
name_maps_english_numbers['flags'] = [['english_number'] for i in range(len(name_maps_english_numbers))]
# name_maps_english_numbers['sub_type'] = '?'

# fractions:
name_maps_fractions = _prep_name_map(name_maps_fractions)
name_maps_fractions['type'] = 'number'
name_maps_fractions['flags'] = [['unicode_fraction'] for i in range(len(name_maps_fractions))]
name_maps_fractions['sub_type'] = 'fraction'
# volume
name_maps_volume = _prep_name_map(name_maps_volume)
name_maps_volume['type'] = 'unit'
name_maps_volume['sub_type'] = 'volume'
# weight
name_maps_weight = _prep_name_map(name_maps_weight)
name_maps_weight['type'] = 'unit'
name_maps_weight['sub_type'] = 'volume'

name_maps = pd.concat([name_maps_fractions, name_maps_english_numbers, name_maps_volume, name_maps_weight])


# sub-types:
# MULTIPLICATIVE:
# - fraction
# - float
# - integer
# OTHER
# - degrees
# - pre_fraction_integer
# - step_number (1., 2., 3....)
# - percent, e.g. '2%'
# UNITS
# - pcs ('package', 'scoops', etc.)
# - volume, metric
# - volume, imperial
# - weight
# TEXT
# - ingredient
# - header
# - text