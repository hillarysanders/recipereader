import itertools
from num2words import num2words
import re
import pandas as pd
from . import utils

def parse_ingredient_line(line = '2 and a half egg yolks, whisked'):

    def clean_line(line):
        # remove periods:
        line = line.replace('.', '')
        # add whitespace padding:
        line = ' {} '.format(line)
        # remove double+ whitespaces:
        line = re.sub(' +', ' ', line)
        return line

    def find_matches(line, name_maps, key='numbers'):
        pattern = '|'.join(conv.names[key])
        # finds non-overlapping matches to our (sorted!) long joined pattern:
        matches = list(re.finditer(pattern, line))

        # base record data frame:
        out = pd.DataFrame(columns=['start', 'end', 'pattern', 'replacement', 'oldline', 'newline'])
        for match in matches:
            start = match.start()
            end = match.end()
            # grab what actually caused the hit:
            pattern = line[start:end]
            # grab the relevant dict:
            dd = [d for d in name_maps if pattern in d['names']]
            if len(dd) > 0:
                if len(dd) > 1:
                    print 'warning: >1 hits to a string... Probably fine though.\n\t' + '\n\t'.join(map(str, dd))
                d = dd[0]
                if key == 'numbers':
                    replacement = d['name']
                else:
                    replacement = '__{}_OR_{}__'.format(d['singular'], d['plural'])

                oldline = line
                line = oldline[:start] + replacement + oldline[end:]
                out.loc[len(out), :] = [start, end, pattern, replacement, oldline, line]

        return out


    conv = Conversions()
    # first, save the original line:
    original_line = line
    line = clean_line(line)
    number_hits = find_matches(line=line, name_maps=conv.name_maps_numbers, key='numbers')
    volume_hits = find_matches(line=line, name_maps=conv.name_maps_volume, key='volume')
    weight_hits = find_matches(line=line, name_maps=conv.name_maps_weight, key='weight')
    # for weight and volume hits, the preceding numbers can inform plurality.
    # todo 1) Make sure none of these hits overlap. If they do, shout out a warning. Show these as highlights in the UI.
    # todo 2) Make a conversion matrix for weight and volume and in-between (liters?).
    # todo 3) Maybe have the parsed lines materialize in the form (on the right side) as the user is typing.
    # todo      then maybe they can fix any parsing mistakes (highlight ones that spout warnings?)
    # todo 4) Add on a widget in the recipe view or edit page to change units (each ingredient? all ingredients?)
    # todo 5) Flag the longest substring apart from ^^ to be the 'ingredient' after removing e.g. 'and', etc.
    # tod       Simple as that for now.
    # todo 6) Change recipe data table to encompass all this information


# when you get onto directions instead of ingredients.... how do you differentiate between numbers for time
# and numbers for amounts? :) That'll be a bit tricky.


class Conversions:
    # TODO! ok this shouldn't be list of dicts it makes it super slow. should be dict of dicts... change.
    # TODO! Or actually... hm. dataframe might be faster. Figure out and implement.
    # todo yeah ok so I think you can keeps the list of dicts, just transform in __init__ to dataframe of
    # todo repeated name info. Then you just add the row into out in find_matches() above.
    name_maps_numbers = [
        dict(names=['a half', 'one half', '1/2', '.5', 'halves'],
             name='1/2'),
        dict(names=['a quarter', 'one quarter', '1/4', '.25', 'a forth', 'quarters'],
             name='1/4'),
        dict(names=['a fifth', 'one fifth', '1/5', '.2', 'a fifth', 'fifths'],
             name='1/4'),
        dict(names=['one third', 'a third', '1/3', 'thirds'],
             name='1/3'),
        dict(names=['one sixth', 'a sixth', '1/6', 'sixths'],
             name='1/6'),
        dict(names=['one eighth', 'an eighth', '1/8', 'eighths'],
             name='1/8'),
        dict(names=['the whole', 'a whole', 'one'],
             name='1')
    ]
    # anything above 1 uses num_to_words
    name_maps_volume = [
        dict(names=['teaspoon', 'tsp', 't'],
             singular='teaspoon',
             plural='tsp.'),
        dict(names=['tablespoon', 'tbsp', 'tbls', 'tbs', 'T'],
             singular='tablespoon',
             plural='tbsp.'),
        dict(names=['fluid ounce', 'fluid oz', 'ounce (fluid)', 'fl oz'],
             singular='fluid ounce',
             plural='fluid oz.'),
        dict(names=['cup'],
             singular='cup',
             plural='cups'),
        dict(names=['pint'],
             singular='pint',
             plural='pints'),  # technically pts. but nobody knows that
        dict(names=['quart'],
             singular='quart',
             plural='quarts'),
        dict(names=['gallon'],
             singular='gallon',
             plural='gallons'),
        dict(names=['liter', 'litre', 'ltr', 'lt', 'l'],
             singular='liter',
             plural='liters'),
        dict(names=['milliliter', 'millilitre', 'ml'],
             singular='milliliter',
             plural='ml')
        ]
    name_maps_weight = [
        dict(names=['gr', 'g', 'grm', 'gram'],
             singular='gram',
             plural='grams'),
        dict(names=['kg', 'kilogram'],
             singular='kg',
             plural='kilograms'),
        dict(names=['milligram', 'mg'],
             singular='milligram',
             plural='mg'),
        dict(names=['lb', 'pound'],
             singular='lb.',
             plural='lbs.'),
        dict(names=['oz', 'ounce', 'onze', 'onza'],
             singular='ounce',
             plural='oz.')
    ]

    def __init__(self):
        # use num2words:
        self._extend_number_name_maps()
        # capitalize stuff:
        self.name_maps_numbers = self._extend_names_with_capitalization(self.name_maps_numbers)
        self.name_maps_volume = self._extend_names_with_capitalization(self.name_maps_volume)
        self.name_maps_weight = self._extend_names_with_capitalization(self.name_maps_weight)
        # add spaces:
        self.name_maps_numbers = self._add_spaces_to_sides(self.name_maps_numbers)
        self.name_maps_weight = self._add_spaces_to_sides(self.name_maps_weight)
        self.name_maps_volume = self._add_spaces_to_sides(self.name_maps_volume)
        # aggregate the names:
        self.names = self._aggregate_names()

    def __str__(self):
        return 'Unit & number conversions class instance.'

    def _add_spaces_to_sides(self, name_maps):
        for i in range(len(name_maps)):
            name_maps[i]['names'] = [' {} '.format(n) for n in name_maps[i]['names']]
        return name_maps

    def _extend_number_name_maps(self, n=1000):
        for i in range(2, n):
            el = dict(names=[num2words(i), str(i)], name=str(i))
            if (i % 12) == 0:
                # two dozen, etc...
                el['names'].extend(['{} dozen'.format(num2words(i/12))])

                if i==12:
                    # include 'a dozen'
                    el['names'].extend(['a dozen'])

            self.name_maps_numbers.extend([el])

    def _extend_names_with_capitalization(self, name_maps):
        for d in name_maps:
            replacement = d['names']
            capitalized = [el.capitalize() for el in replacement if el != 't']
            upper = [el.upper() for el in replacement if el != 't']
            replacement.extend(capitalized)
            replacement.extend(upper)
            replacement = list(set(replacement))

        return name_maps

    def _aggregate_names(self):
        # could do this scalable w/ dict comprehensions if you ever wanted to add conversion types.
        def flatten_names(name_maps):
            return list(utils.flatten([d['names'] for d in name_maps]))

        names = dict(
            volume=flatten_names(self.name_maps_volume),
            weight=flatten_names(self.name_maps_weight),
            numbers=flatten_names(self.name_maps_numbers)
        )
        names['units'] = list(itertools.chain.from_iterable([names['volume'], names['weight']]))

        return names
