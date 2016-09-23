# coding=utf8
from __future__ import unicode_literals
import pandas as pd
from num2words import num2words
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
         plural='milliliters'),
    dict(pattern=['centiliter', 'centiliters', 'centilitre', 'centilitres', 'cl', 'cl\.'],
         singular='centiliter',
         plural='centiliters'),
    dict(pattern=['st\.', 'stone'],
         singular='stone',
         plural='st.')
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
    dict(pattern=['lb', 'pound', 'lbs', 'pounds', 'lb\.', 'lbs\.'],  # todo pound cake???
         singular='pound',
         plural='lbs.'),
    dict(pattern=['oz', 'ounce', 'onze', 'onza', 'oz\.'],
         singular='ounce',
         plural='oz.')
]

# units that aren't convertible:
name_maps_pcs = [
    dict(pattern=['pcs', 'pieces', 'piece'],
         singular='piece',
         plural='pieces'),
    dict(pattern=['dash', 'dashes'],
         singular='dash',
         plural='dashes'),
    dict(pattern=['handful', 'handfuls'],
         singular='handful',
         plural='handfuls'),
    dict(pattern=['spring', 'sprigs'],
         singular='sprig',
         plural='sprigs'),
    dict(pattern=['scoop', 'scoops'],
         singular='scoop',
         plural='scoops'),
    dict(pattern=['package', 'pkg\.', 'pkg', 'packages', 'pkgs', 'pkgs\.'],
         singular='package',
         plural='packages'),
    dict(pattern=['bag', 'bags'],
         singular='bag',
         plural='bags'),
    dict(pattern=['container', 'containers'],
         singular='container',
         plural='containers'),
    dict(pattern=['can', 'cans'],
         singular='can',
         plural='cans'),
    dict(pattern=['unit', 'units'],
         singular='unit',
         plural='units'),
    dict(pattern=['slice', 'slices'],
         singular='slice',
         plural='slices'),
    dict(pattern=['bunch', 'bunches'],
         singular='bunch',
         plural='bunches'),
    # dict(pattern=[],
    #      singular='',
    #      plural=''),
]

temperature_patterns = pd.DataFrame(dict(pattern=['ºC', 'ºF', 'º', 'degrees']))
temperature_patterns['name'] = temperature_patterns['pattern']
temperature_patterns['type'] = 'temperature'
time_patterns = pd.DataFrame(dict(pattern=['minutes', 'seconds', 'hours', 'minute', 'second', 'hours']))
time_patterns['name'] = time_patterns['pattern']
time_patterns['type'] = 'unit_of_time'
length_patterns = pd.DataFrame(dict(pattern=['inch', 'inches', 'centimeter', 'centimeters',
                                             'millimeter', 'millimeters']))
length_patterns['name'] = length_patterns['pattern']
length_patterns['type'] = 'unit_of_length'


def _name_maps_dict_to_df(name_maps):
    return pd.concat([pd.DataFrame(d) for d in name_maps])


def _prep_name_map(name_maps):
    """
    a name_map in this file is a list of dictionaries, where each
    dict shows a bunch of strings (names) that map to its 'true' (chosen) name.
    e.g. 'T.', 'tablespoon' will all map to 'tbsp.'.
    This function preps all the possible pattern strings by augmenting them
    via capitalization, etc. The transforms the dicts into a nicer to handle dataframe.
    """

    name_maps = name_maps.drop_duplicates('pattern')

    # sort by pattern length:
    name_maps['pattern_length'] = [len(p) for p in name_maps.pattern]
    name_maps = name_maps.sort_values(by=['pattern_length'])
    del name_maps['pattern_length']

    name_maps = name_maps.reset_index(drop=True)
    name_maps = name_maps.set_index('pattern', drop=False)

    return name_maps


def _get_name_maps_english_numbers(n=1000):
    """
    e.g. 'twenty four' = 24.
    :param n:
    :return:
    """
    name_maps_english_num = []
    for i in range(1, n):
        pattern = num2words(i)
        el = dict(pattern=[pattern], name=pattern, value=float(i))
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
name_maps_english_numbers = _prep_name_map(_name_maps_dict_to_df(name_maps_english_numbers))
name_maps_english_numbers['type'] = 'number'
name_maps_english_numbers['sub_type'] = 'english_number'
# name_maps_english_numbers['sub_type'] = '?'

# fractions:
name_maps_fractions = _prep_name_map(_name_maps_dict_to_df(name_maps_fractions))
name_maps_fractions['type'] = 'number'
name_maps_fractions['sub_type'] = 'unicode_fraction'
# volume
name_maps_volume = _prep_name_map(_name_maps_dict_to_df(name_maps_volume))
name_maps_volume['type'] = 'unit'
name_maps_volume['sub_type'] = 'volume'
# weight
name_maps_weight = _prep_name_map(_name_maps_dict_to_df(name_maps_weight))
name_maps_weight['type'] = 'unit'
name_maps_weight['sub_type'] = 'weight'
# non convertible units:
name_maps_pcs = _prep_name_map(_name_maps_dict_to_df(name_maps_pcs))
name_maps_pcs['type'] = 'unit'
name_maps_pcs['sub_type'] = 'pcs'

name_maps = pd.concat([_prep_name_map(temperature_patterns),
                       _prep_name_map(time_patterns),
                       _prep_name_map(length_patterns),
                       name_maps_fractions,
                       name_maps_english_numbers,
                       name_maps_volume,
                       name_maps_weight,
                       name_maps_pcs])

name_maps = name_maps.fillna(value='')


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