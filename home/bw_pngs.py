import os
import pandas as pd
from . import utils

# path_to_images = os.path.join(os.path.dirname(__file__), 'static/home/images/bw_pngs/')
# # path_to_images = 'static/home/images/bw_pngs/'
# thumb_dir = 'thumbnail/'
# med_dir = 'medium/'
# utils.safe_mkdir(path_to_images+thumb_dir)
# utils.safe_mkdir(path_to_images+med_dir)
#
# # first, read in all the names from both dirs and find the intersect of names:
# thumb_files = os.listdir(path_to_images + thumb_dir)
# med_files = os.listdir(path_to_images + med_dir)
# files = list(set(thumb_files + med_files))

# for file in sorted(files):
#     if file != '.DS_Store':
#         fi = file.replace('.png', '')
#         print "'{}',  'key': ['{}'],".format(file, fi)

bw_name_maps = [
    {'file': 'acorn_squash.png',
     'key': ['acorn_squash']},
    {'file': 'almond.png',
     'key': ['almond']},
    {'file': 'apple.png',
     'key': ['apple']},
    {'file': 'artichoke.png',
     'key': ['artichoke']},
    {'file': 'artichoke_2.png',
     'key': ['artichoke']},
    {'file': 'artichoke_heart.png',
     'key': ['artichoke_heart']},
    {'file': 'avocado.png',
     'key': ['avocado']},
    {'file': 'bacon.png',
     'key': ['bacon']},
    {'file': 'baking_powder.png',
     'key': ['baking powder']},
    {'file': 'baking_soda.png',
     'key': ['baking soda']},
    {'file': 'balsamic.png',
     'key': ['balsamic']},
    {'file': 'basil.png',
     'key': ['basil']},
    {'file': 'bay_leaf.png',
     'key': ['bay leaf']},
    {'file': 'beet.png',
     'key': ['beet']},
    {'file': 'bell_pepper.png',
     'key': ['bell pepper']},
    {'file': 'bowtie.png',
     'key': ['bowtie', 'bow-tie', 'bow tie']},
    {'file': 'bread.png',
     'key': ['bread']},
    {'file': 'broccoli.png',
     'key': ['broccoli']},
    {'file': 'butter.png',
     'key': ['butter']},
    {'file': 'butternut_squash.png',
     'key': ['butternut squash']},
    {'file': 'carrot.png',
     'key': ['carrot']},
    {'file': 'cheddar.png',
     'key': ['cheddar']},
    {'file': 'cherr.png',
     'key': ['cherry', 'cherries']},
    {'file': 'cherry_tomato.png',
     'key': ['cherry tomato']},
    {'file': 'chicken.png',
     'key': ['chicken']},
    {'file': 'cilantro.png',
     'key': ['cilantro']},
    {'file': 'coriander.png',
     'key': ['coriander']},
    {'file': 'cupcake.png',
     'key': ['cupcake']},
    {'file': 'egg.png',
     'key': ['egg']},
    # {'file': 'egg_1.png',
    #  'key': ['egg']},
    {'file': 'enoki_mushroom.png',
     'key': ['enoki mushroom']},
    {'file': 'flour.png',
     'key': ['flour']},
    {'file': 'green_onion.png',
     'key': ['green onion', 'scallion']},
    {'file': 'half_and_half.png',
     'key': ['half and half', 'half & half', 'half n half', "half n' half"]},
    {'file': 'halibut.png',
     'key': ['halibut', 'fish fillet']},
    {'file': 'jam.png',
     'key': ['jam', 'preserves', 'conserve', 'jelly', 'marmalade']},
    {'file': 'kabocha.png',
     'key': ['kabocha', 'winter squash']},
    {'file': 'kiwi.png',
     'key': ['kiwi']},
    {'file': 'lemon.png',
     'key': ['lemon']},
    {'file': 'lemon_1.png',
     'key': ['lemon']},
    {'file': 'lettuce.png',
     'key': ['lettuce']},
    {'file': 'lime_leaf.png',
     'key': ['lime leaf']},
    {'file': 'lychee.png',
     'key': ['lychee']},
    {'file': 'maggi.png',
     'key': ['maggi']},
    {'file': 'mangosteen.png',
     'key': ['mangosteen']},
    {'file': 'melon.png',
     'key': ['melon']},
    {'file': 'mint.png',
     'key': ['mint']},
    {'file': 'mozzerella.png',
     'key': ['mozzerella']},
    {'file': 'mushroom.png',
     'key': ['mushroom']},
    {'file': 'oyster_mushroom.png',
     'key': ['oyster mushroom']},
    {'file': 'pasta.png',
     'key': ['pasta']},
    {'file': 'peach.png',
     'key': ['peach']},
    {'file': 'penne.png',
     'key': ['penne']},
    {'file': 'plum.png',
     'key': ['plum']},
    {'file': 'plum_2.png',
     'key': ['plum']},
    {'file': 'plum_3.png',
     'key': ['plum']},
    {'file': 'salt.png',
     'key': ['salt']},
    {'file': 'sardine.png',
     'key': ['sardine']},
    {'file': 'strawberr.png',
     'key': ['strawberry', 'strawberries']},
    {'file': 'strawberr_2.png',
     'key': ['strawberry', 'strawberries']},
    {'file': 'sugar.png',
     'key': ['sugar']},
    {'file': 'sweet_dumpling_squash.png',
     'key': ['sweet dumpling squash']},
    {'file': 'turnip.png',
     'key': ['turnip']},
    # {'file': 'unknown.png',  'key': ['unknown']},
    # {'file': 'unknown_1.png',  'key': ['unknown_1']},
    {'file': 'vanilla.png',
     'key': ['vanilla']},
    {'file': 'water.png',
     'key': ['water']},
    {'file': 'zucchini.png',
     'key': ['zucchini']}
]

bw_name_maps = pd.concat([pd.DataFrame(d) for d in bw_name_maps])
# bw_name_maps = bw_name_maps.loc[[f in files for f in bw_name_maps['file']], :]
# bw_name_maps['thumb'] = path_to_images + thumb_dir + bw_name_maps['file']
# bw_name_maps['med'] = path_to_images + med_dir + bw_name_maps['file']
# bw_name_maps['size'] = [os.path.getsize(path) for path in bw_name_maps['med']]
# bw_name_maps['thumb_size'] = [os.path.getsize(path) for path in bw_name_maps['thumb']]
# bw_name_maps = bw_name_maps.sort_values(by='size', axis=0, ascending=False)
bw_name_maps.index = range(len(bw_name_maps))