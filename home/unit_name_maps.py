# coding=utf8
from __future__ import unicode_literals
import pandas as pd
from num2words import num2words
"""
Base conversion dictionaries that conversions.py will use to build nicely formatted conversion objects.
Not meant to be used directly.
"""


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
    name_maps = name_maps.sort_values(by=['pattern_length'], ascending=False)
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


name_maps_fractions = [
    # don't want to match to... half and half, half chopped, etc
    dict(pattern=['a half', 'half of a', 'one half', '1/2', '\.5', '½'],
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
         value=1./3),
    dict(pattern=['one sixth', 'a sixth', '1/6', 'sixths', '⅙'],
         name='⅙',
         value=1./6),
    dict(pattern=['5/6', '⅚'],
         name='⅚',
         value=5./6),
    dict(pattern=['one eighth', 'an eighth', '1/8', 'eighths', '⅛'],
         name='⅛',
         value=1./8),
    dict(pattern=['⅜', '3/8'],
         name='⅜',
         value=3./8),
    dict(pattern=['⅔', '2/3'],
         name='⅔',
         value=2./3),
    dict(pattern=['¾', '3/4'],
         name='¾',
         value=3./4)
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
    dict(pattern=['cup', 'cups', 'c\.'],
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
         plural='ml'),
    dict(pattern=['centiliter', 'centiliters', 'centilitre', 'centilitres', 'cl', 'cl\.'],
         singular='centiliter',
         plural='cl'),
    dict(pattern=['st\.', 'stone'],
         singular='stone',
         plural='st.')
]

name_maps_weight = [
    dict(pattern=['gr', 'g', 'grm', 'gram', 'grams', 'g\.', 'gr\.'],
         singular='gram',
         plural='grams'),
    dict(pattern=['kg', 'kilogram', 'kilograms', 'kg\.'],
         singular='kilogram',
         plural='kg'),
    dict(pattern=['milligram', 'mg', 'milligram', 'mg\.'],
         singular='milligram',
         plural='mg'),
    dict(pattern=['lb', 'pound', 'lbs', 'pounds', 'lb\.', 'lbs\.'],  # todo pound cake???
         singular='pound',
         plural='lbs.'),
    dict(pattern=['oz', 'ounce', 'ounces', 'onze', 'onza', 'oz\.'],
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
    dict(pattern=['loaf', 'loaves'],
         singular='loaf',
         plural='loaves'),
    dict(pattern=['bunch', 'bunches'],
         singular='bunch',
         plural='bunches')
    # dict(pattern=[],
    #      singular='',
    #      plural=''),
]
# ingredients that are generally mentioned by name (e.g. '2 eggs'), not by unit:
for ing in ['apple', 'banana', 'egg', 'apricot', 'aubergine', 'eggplant', 'avocado', 'beet', 'yam',
            'carrot', 'clementine', 'courgette', 'date', 'endive', 'fennel', 'fig', 'garlic head',
            'green bean', 'guava', 'honeydew melon', 'watermelon', 'jerusalem artichoke', 'artichoke',
            'kiwi', 'leek', 'lemon', 'lime', 'mango', 'mushroom', 'nectarine', 'nut', 'olive', 'orange',
            'peanut', 'pear', 'pineapple', 'pumpkin', 'quince', 'raisin', 'rhubarb', 'satsuma',
            'sweet potato', 'potato', 'tomato', 'turnip', 'plum', 'zucchini',
            'chicken thigh', 'chicken breast',

            'clove', 'shallot', 'chunk', 'knob',

            'serving']:
    name_maps_pcs.append(dict(pattern=[ing, '{}s'.format(ing)],
                              singular=ing,
                              plural='{}s'.format(ing)))
for ing in ['radish']:
    name_maps_pcs.append(dict(pattern=[ing, '{}es'.format(ing)],
                              singular=ing,
                              plural='{}es'.format(ing)))


temperature_patterns = pd.DataFrame(dict(pattern=['ºC', 'ºF', 'º', 'degrees'],
                                         type='unit', sub_type='temperature'))
temperature_patterns['name'] = temperature_patterns['pattern']

time_patterns = pd.DataFrame(dict(pattern=['minutes', 'seconds', 'hours', 'minute', 'second', 'hours'],
                                  type='unit', sub_type='time'))
time_patterns['name'] = time_patterns['pattern']

length_patterns = pd.DataFrame(dict(pattern=['inch', 'inches', 'centimeter', 'centimeters',
                                             'millimeter', 'millimeters'],
                                    type='unit', sub_type='length'))
length_patterns['name'] = length_patterns['pattern']

percent_patters = pd.DataFrame(dict(pattern=['%', 'percent'], name=['%', 'percent'],
                                    type='unit', sub_type='percent'))


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
name_maps_fractions['sub_type'] = 'fraction'

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
                       _prep_name_map(percent_patters),
                       name_maps_fractions,
                       name_maps_english_numbers,
                       name_maps_volume,
                       name_maps_weight,
                       name_maps_pcs])

name_maps['sister_idx'] = None
name_maps = name_maps.fillna(value='')

multipliable = dict(
    temperature=False,
    temperature_number=False,
    length=False,
    length_number=False,
    percent=False,
    percent_number=False,
    time=False,
    time_number=False,
    each_number=False,
    dimension=False,
    line_number=False,
    hashtag_number=False,
    package=False,
    package_number=False,
    weight=True,
    volume=True,
    pcs=True,
    int_fraction=True,
    int=True,
    fraction=True,
    float=True,
    english_number=True,
    range=True
)

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
    # package_number
    # each_number
    # dimensions

    # ## UNIT
    # weight
    # volume
    # pcs

    # ### list of types:
    # unit
    # number
    # text