import pandas as pd
import numpy as np
import logging as log
from .utils import most_common
# anything above 1 uses num_to_words


class UnitConversions:
    """
    This class helps handle unit conversion dictionaries.
    Using this class is handy because it will check your conversions for consistency, when
    you use self.check_conversion_consistency(). check_conversion_consistency() will tell you
    if you can convert from X to Y but not from Y to X, give you suggestions, and warn you
    when conversions do not convert - e.g. if X to Y != 1 / Y to X).
    """

    # types of units:
    units = dict(mass=['kilogram', 'gram', 'milligram', 'ounce', 'pound', 'stone'],
                 volume_us=['teaspoon', 'tablespoon', 'fluid ounce', 'cup', 'pint', 'quart', 'gallon'],
                 volume_metric=['liter', 'milliliter', 'centiliter'],
                 pcs=['pcs'])
    # conversions between unit types:
    conversions_between = {
        'volume_us': {
            'mass': {
                'from': 'cup',
                'to': 'gram',
                'conversions': {
                    'water': 236.59,
                    'flour': 125.,
                    'brown sugar': 220.,
                    'powdered sugar': 110.,
                    'sugar': 200.,
                    'milk': 230.,
                    'cornstarch': 110.,
                    'cocoa powder': 91.,
                    'baking powder': 220.,
                    'baking soda': 220.,
                    'salt': 288.,
                    'butter': 220.,
                    'corn syrup': 310.,
                    'molasses': 260.,
                    'honey': 310.,
                    'oil': 200.
                }
            },
            'volume_metric': {
                'from': 'cup',
                'to': 'liter',
                'conversion': 4.22675
            }
        },
        'volume_metric': {
            'mass': {
                'from': 'liter',
                'to': 'gram',
                'conversions': {
                    'water': 1000.,
                    'flour': 125.*4.22675,
                    'brown sugar': 220.*4.22675,
                    'powdered sugar': 110.*4.22675,
                    'sugar': 200.*4.22675,
                    'milk': 230.*4.22675,
                    'cornstarch': 110.*4.22675,
                    'cocoa powder': 91.*4.22675,
                    'baking powder': 220.*4.22675,
                    'baking soda': 220.*4.22675,
                    'salt': 288.*4.22675,
                    'butter': 220.*4.22675,
                    'corn syrup': 310.*4.22675,
                    'molasses': 260.*4.22675,
                    'honey': 310.*4.22675,
                    'oil': 200.*4.22675
                }
            },
            'volume_us': {
                'from': 'liter',
                'to': 'cup',
                'conversion': 0.236588
            }
        },
        'mass': {
            'volume_us': {
                'from': 'gram',
                'to': 'cup',
                'conversions': {
                    'water': 1./236.59,
                    'flour': 1./125.,
                    'brown sugar': 1./220.,
                    'powdered sugar': 1./110.,
                    'sugar': 1./200.,
                    'milk': 1./230.,
                    'cornstarch': 1./110.,
                    'cocoa powder': 1./91.,
                    'baking powder': 1./220.,
                    'baking soda': 1./220.,
                    'salt': 1./288.,
                    'butter': 1./220.,
                    'corn syrup': 1./310.,
                    'molasses': 1./260.,
                    'honey': 1./310.,
                    'oil': 1./200.
                }
            },
            'volume_metric': {
                'from': 'gram',
                'to': 'liter',
                'conversions': {
                    'water': 1./1000.,
                    'flour': 1./125.*4.22675,
                    'brown sugar': 1./220.*4.22675,
                    'powdered sugar': 1./110.*4.22675,
                    'sugar': 1./200.*4.22675,
                    'milk': 1./230.*4.22675,
                    'cornstarch': 1./110.*4.22675,
                    'cocoa powder': 1./91.*4.22675,
                    'baking powder': 1./220.*4.22675,
                    'baking soda': 1./220.*4.22675,
                    'salt': 1./288.*4.22675,
                    'butter': 1./220.*4.22675,
                    'corn syrup': 1./310.*4.22675,
                    'molasses': 1./260.*4.22675,
                    'honey': 1./310.*4.22675,
                    'oil': 1./200.*4.22675
                }
            }
        }
    }

    # if you have fewer than MIN unit values, then convert to smaller_unit
    # if you have over or equal to MAX unit values, then covert to larger_unit
    thresholds = {
        'milligram': {
            'min': -np.Inf,
            'smaller_unit': None,
            'max': 1000.,
            'larger_unit': 'gram'
        },
        'gram': {
            'min': 1.,
            'smaller_unit': 'milligram',
            'max': 1000.,
            'larger_unit': 'kilogram'
        },
        'kilogram': {
            'min': 1.,
            'smaller_unit': 'gram',
            'max': np.Inf,
            'larger_unit': None
        },
        'ounce': {
            'min': -np.Inf,
            'smaller_unit': None,
            'max': 32.,
            'larger_unit': 'pound'
        },
        'pound': {
            'min': 1.,
            'smaller_unit': 'ounce',
            'max': np.Inf,
            'larger_unit': None
        },
        'fluid ounce': {
            'min': -np.Inf,
            'smaller_unit': None,
            'max': 8.,
            'larger_unit': 'cup'
        },
        'teaspoon': {
            'min': -np.Inf,
            'smaller_unit': None,
            'max': 3.,
            'larger_unit': 'tablespoon'
        },
        'tablespoon': {
            'min': 1.,
            'smaller_unit': 'teaspoon',
            'max': 8,
            'larger_unit': 'cup'
        },
        'cup': {
            'min': 1./8,
            'smaller_unit': 'tablespoon',
            # usually people like to stay in cups over pints / quarts
            'max': np.Inf,
            'larger_unit': None
        },
        'pint': {
            'min': 1.,
            'smaller_unit': 'cup',
            'max': 2,
            'larger_unit': 'quart'
        },
        'quart': {
            'min': 1.,
            'smaller_unit': 'cup',
            'max': 4.,
            'larger_unit': 'gallon'
        },
        'gallon': {
            'min': 1.,
            'smaller_unit': 'cup',
            'max': np.Inf,
            'larger_unit': None
        },
        'milliliter': {
            'min': -np.Inf,
            'smaller_unit': None,
            'max': 1000.,
            'larger_unit': 'liter'
        },
        'centiliter': {
            'min': 1.,
            'smaller_unit': 'milliliter',
            'max': 100.,
            'larger_unit': 'liter'
        },
        'liter': {
            'min': 1.,
            'smaller_unit': 'milliliter',
            'max': np.Inf,
            'larger_unit': None
        },
        'pcs': {
            'min': -np.Inf,
            'smaller_unit': None,
            'max': np.Inf,
            'larger_unit': None
        }
    }
    # conversions within unit types:
    conversions = {
        # MASS
        'kilogram': {
            'milligram': 1e+6,
            'gram': 1000.0,
            'kilogram': 1.0,
            'ounce': 35.274,
            'pound': 2.20462
        },
        'gram': {
            'milligram': 1000,
            'gram': 1.0,
            'kilogram': 1 / 1000.0,
            'ounce': 0.035274,
            'pound': 0.00220462},
        'milligram': {
            'milligram': 1.0,
            'gram': 1e-3,
            'kilogram': 1e-6,
            'ounce': 3.5274e-5,
            'pound': 2.2046e-6
        },
        'ounce': {
            'milligram': 28349.5,
            'gram': 28.3495,
            'kilogram': 0.0283495,
            'ounce': 1.0,
            'pound': 0.0625
        },
        'pound': {
            'milligram': 453592.,
            'gram': 453.592,
            'kilogram': 0.453592,
            'ounce': 16.0,
            'pound': 1.0
        },
        # VOLUME:
        # teaspoon, tablespoon, fluid ounce, cup, pint, quart, gallon, liter, milliliter, centiliter
        # US (IMPERIAL) VOLUME:
        'teaspoon': {
            'teaspoon': 1.,
            'fluid ounce': 1./6,
            'tablespoon': 1/3.,
            'cup': 1./48.,
            'pint': 1./96,
            'quart': 1./192,
            'gallon': .25/192,
            'liter': 0.00492892,
            'milliliter': 4.92892,
            'centiliter': 0.492892
        },
        'tablespoon': {
            'teaspoon': 3.,
            'fluid ounce': 1./2,
            'tablespoon': 1.,
            'cup': 1./16,
            'pint': 1./32,
            'quart': 1./64,
            'gallon': 1./256,
            'liter': 0.0147868,
            'milliliter': 14.7868,
            'centiliter': 1.47868
        },
        'fluid ounce': {
            'teaspoon': 6.,
            'fluid ounce': 1.,
            'tablespoon': 2.,
            'cup': 1./8,
            'pint': 1./16,
            'quart': 1./32,
            'gallon': 1./128,
            'liter': 0.0295735,
            'milliliter': 29.5735,
            'centiliter': 2.95735
        },
        'cup': {
            'teaspoon': 48.,
            'fluid ounce': 8.,
            'tablespoon': 16.,
            'cup': 1.,
            'pint': 1./2,
            'quart': 1./4,
            'gallon': 1./16,
            'liter': 0.236588,
            'milliliter': 236.588,
            'centiliter': 23.6588
        },
        'pint': {
            'teaspoon': 96.,
            'fluid ounce': 16.,
            'tablespoon': 32.,
            'cup': 2.,
            'pint': 1,
            'quart': 1./2,
            'gallon': 1./8,
            'liter': 0.473176,
            'milliliter': 473.176,
            'centiliter': 47.3176
        },
        'quart': {
            'teaspoon': 192.,
            'fluid ounce': 32.,
            'tablespoon': 64.,
            'cup': 4.,
            'pint': 2,
            'quart': 1.,
            'gallon': 1./4,
            'liter': 0.946353,
            'milliliter': 946.353,
            'centiliter': 94.6353
        },
        'gallon': {
            'teaspoon': 768.,
            'fluid ounce': 128.,
            'tablespoon': 256.,
            'cup': 16.,
            'pint': 8.,
            'quart': 4.,
            'gallon': 1.,
            'liter': 3.78541,
            'milliliter': 3785.41,
            'centiliter': 378.541
        },
        # VOLUME: METRIC
        'milliliter': {
            'teaspoon': 0.202884,
            'fluid ounce': 0.033814,
            'tablespoon': 0.067628,
            'cup': 0.00422675,
            'pint': 0.00211338,
            'quart': 0.00105669,
            'gallon': 0.000264172,
            'liter': .001,
            'milliliter': 1.,
            'centiliter': .1
        },
        'centiliter': {
            'teaspoon': 2.02884,
            'fluid ounce': 0.33814,
            'tablespoon': 0.67628,
            'cup': .0422675,
            'pint': .0211338,
            'quart': .0105669,
            'gallon': .00264172,
            'liter': .01,
            'milliliter': 10.,
            'centiliter': 1.
        },
        'liter': {
            'teaspoon': 202.884,
            'fluid ounce': 33.814,
            'tablespoon': 67.628,
            'cup': 4.22675,
            'pint': 2.11338,
            'quart': 1.05669,
            'gallon': 0.264172,
            'liter': 1.,
            'milliliter': 1000.0,
            'centiliter': 100.0
        },
        # OTHER:
        'pcs': {'pcs': 1.0}
    }

    def __init__(self):
        pass

    def get_inverse_conversions(self, unit):
        inverse = {}
        for key, value in self.conversions.iteritems():
            if unit in value.keys():
                inverse[key] = 1./value[unit]
        return inverse

    def check_conversion_consistency(self, relative_tolerance=.001):
        for unit_from, units_to in self.conversions.iteritems():
            for unit_to in units_to.keys():
                # first check if there's even an inverse conversion dict:
                if self.conversions.get(unit_to) is None:
                    log.debug('{} can be converted to {}, but not the other way around. Consider augmenting.'.format(
                        unit_from, unit_to
                    ))
                    log.debug('Consider adding "'+unit_to+'": ' + str(self.get_inverse_conversions(unit_to)))
                # then check if the inverse mapping exists:
                elif self.conversions[unit_to].get(unit_from) is None:
                    log.debug('{} can be converted to {}, but not the other way around. Consider augmenting.'.format(
                        unit_from, unit_to
                    ))
                    log.debug("Consider augmenting self.conversions[{}] to include '{}': {}".format(
                        unit_to, unit_from, 1./self.conversions[unit_from][unit_to]))
                else:
                    if not is_close(self.conversions[unit_from][unit_to],
                                    1./self.conversions[unit_to][unit_from],
                                    relative_tolerance=relative_tolerance):
                        msg = 'conversions[{}][{}] = {} conflicts with\n\t1/conversions[{}][{}] = 1 / {} \n\t= {})'
                        log.error(msg.format(
                            unit_from, unit_to, self.conversions[unit_from][unit_to],
                            unit_to, unit_from, self.conversions[unit_to][unit_from],
                            1.0/self.conversions[unit_to][unit_from]
                        ))

CONVERSION_FACTORS = UnitConversions()


def is_close(a, b, relative_tolerance=.0001, absolute_tolerance=None):
    """
    This function is used when you want to compare the almost-equality of two numbers that should be very similar
    (e.g. equal to 4 digits), but not exact. Just rounding with np.round() doesn't work well.
    :param a: int or float
    :param b: int or float
    :param relative_tolerance: int or float - the relative amount of error you'll allow
    :param absolute_tolerance: int or float - the absolute amound of error you'll allow
    :return: boolean, true or false
    """

    return abs(a-b) <= max(relative_tolerance * max(abs(a), abs(b)), absolute_tolerance)


def get_conversion(unit, wanted_unit, conversion_factors=CONVERSION_FACTORS.conversions):
    """
    Simple helper function to convert_units, but can also be used separately. Like dict.get()
    but with two levels (unit and wanted unit), and returns np.nan instead of None if there
    is no match.
    :param unit: original unit
    :param wanted_unit: the unit to convert to
    :param conversion_factors: dictionary of conversion factors, e.g. UnitConversions().conversions
    :return: conversion float, or np.nan if no conversion existed
    """
    if unit not in conversion_factors.keys():
        return np.nan
    elif wanted_unit not in conversion_factors[unit].keys():
        return np.nan
    else:
        return float(conversion_factors[unit][wanted_unit])


def convert_units(spec_df,
                  unit_col='size_units',
                  size_col='size',
                  price_col='price',
                  wanted_unit='most common',
                  wanted_size=None,
                  nan_if_conversion_is_not_possible=True,
                  conversion_factors=CONVERSION_FACTORS.conversions):
    """
    :param spec_df: dataframe of observations
    :param unit_col: str - column name that represents size_units
    :param size_col: str - column name that represents size_units
    :param price_col: str - column name that represents price. Only relevant if wanted_size is not None,
        because if wanted_size is None, normalized_price is not created, just normalized_size_unit.
    :param wanted_unit: str - optional, the unit you want to coerce to. If 'most common', this function
        will coerce to the most common size unit.
    :param wanted_size: str - optional, the size you want to coerce to. If 'most common', this function
        will coerce to the most common size per coerced size unit. Note that nan_if_conversion_is_not_possible
        is recommended to be set to False in this case, else you risk coercing to size np.nan if
        wanted_unit != 'most_common'.
        If wanted_size = None, only units will be
        converted - so there will be a normalized_size column in the returned dataframe, from the effect of
        the unit conversion, but they may be different. Similarly, there will only be a normalized_price
        column if there was a specified wanted_size, because otherwise prices will remain unaffected.
    :return: a dataframe of converted values. Each column will be named "converted_{}", where {} is the
        relevant original column name.

    Example Code:
    .. code-block::
        spec_df = pd.DataFrame(dict(
            size_unit=['gram', 'gram', 'kilogram', 'gram', 'kilogram', 'pound', 'ounce', 'milliliter'],
            size=[1000, 1000, 1, 1, 1, 1, 20, 100],
            quantity=[1, 1, 1, 1000, 1, 1, 1, 1],
            price=[10, 11, 9, 12, 12, 5, 10, 10]))
        spec_df['total_size'] = spec_df.size*spec_df.quantity

        # convert units, where the goal unit is 'kilogram'
        convert_units(spec_df, size_col='total_size', unit_col='size_unit', wanted_unit='kilogram', wanted_size=1)
        # convert units, where the goal unit is the most common unit (wanted_size_unit='most common'):
        convert_units(spec_df, size_col='total_size', unit_col='size_unit', wanted_size=1)
        # convert units, where size and price aren't normalized, just units:
        convert_units(spec_df, size_col='total_size', unit_col='size_unit')

        # what if you want to convert both size AND quantity?
        converted_sizes = convert_units(spec_df, size_col='size', unit_col='size_unit', wanted_unit='gram', wanted_size=1000)
        spec_df = pd.concat([converted_sizes, spec_df], axis=1)
        converted_quantity = convert_units(spec_df, size_col='quantity', unit_col='normalized_size_unit',
                                           wanted_unit='gram', wanted_size=1, price_col='normalized_price')
        spec_df['normalized_price'] = converted_quantity['normalized_normalized_price']
        spec_df['normalized_quantity'] = converted_quantity['normalized_quantity']

    """
    # if wanted unit is none, make it the most common unit value:
    if wanted_unit == 'most common':
        wanted_unit = most_common(spec_df[unit_col])
        log.debug('Coercing units to the most common unit: {}.'.format(wanted_unit))

    # get the conversion rates from each unit to the wanted unit:
    conversion = spec_df.groupby(unit_col)[unit_col].transform(
        lambda unit: get_conversion(unit=unit.values[0],
                                    wanted_unit=wanted_unit,
                                    conversion_factors=conversion_factors)
    )

    # make some columns that'll be used for the return object:
    conv_size_col = 'normalized_{}'.format(size_col)
    conv_unit_col = 'normalized_{}'.format(unit_col)
    conv_price_col = 'normalized_{}'.format(price_col)
    # apply the conversions:
    converted = pd.DataFrame({
        conv_size_col: spec_df[size_col]*conversion,
        conv_unit_col: [np.nan if b else wanted_unit for b in conversion.isnull()]
    })

    if not nan_if_conversion_is_not_possible:
        nan_idx = converted.isnull().apply(any, axis=1)
        converted.loc[nan_idx, conv_size_col] = spec_df.loc[nan_idx, size_col]
        converted.loc[nan_idx, conv_unit_col] = spec_df.loc[nan_idx, unit_col]

    if wanted_size == 'most common':
        wanted_size = converted.groupby(conv_unit_col)[conv_size_col].transform(most_common)

    if wanted_size is not None:
        size_conversion = wanted_size / converted[conv_size_col]
        converted[conv_size_col] *= size_conversion
        converted[conv_price_col] = size_conversion*spec_df[price_col]
        if not nan_if_conversion_is_not_possible:
            converted.loc[nan_idx, conv_price_col] = spec_df.loc[nan_idx, price_col]

    return converted



# names = ["catty", "g", "kg", "lb", "oz", "ltr", "ml", "l"]
# # if COUNTRY = CHINA, then catty is 500 g, not 600, and a tael is 10 catties, not 16.
# conversion_matrix = pd.DataFrame(dict(
#       #      "catty"       "g"         "kg"     "lb"          "oz"     "ltr"     "ml"     "l"     "tael"
#       catty=[1,         600,       .6,        1.323,       21.168,    .6 ,      600,     .6], #catty
#       g=    [1/600,     1,         .001,      0.002205,    0.03527,   .001,     1,       .001],  #g
#       kg=   [1/.6,      1000,      1,         2.205,       35.27,     1,        1000,    1],  #kg
#       lb=   [1/1.323,   453.592,   1/2.205,   1,           16,        .4536,    453.6,   .4536],  #lb
#       oz=   [1/21.168,  1/0.03527, 1/35.27,   1/16,        1,         0.02957,  29.57,   .02957],  #oz
#       ltr=  [1/.6,      1000,      1,         1/.4536,     1/0.02957, 1,        1000,    1],  #ltr
#       ml=   [1/600,     1,         .001,      1/453.6,     1/29.57,   .001,     1,       .001],  #ml
#       l=    [1/.6,      1000,      1,         1/.4536,     1/0.02957, 1,        1000,    1]),  #l
#     index=names)
#