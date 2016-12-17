from autocomplete_light import shortcuts as al
from . import models

al.register(models.RecipeTags,
            search_fields=["^tag"],
            attrs={
                "placeholder": "Recipe tags",
                "data-autocomplete-minimum-characters": 1,
            },
            widget_attrs={
                "data-widget-maximum-values": 4,
                "class": "modern-style",
            },
            )
