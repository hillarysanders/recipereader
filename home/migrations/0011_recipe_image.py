# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-07 04:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_remove_recipe_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(blank=True, upload_to='home/images/uploaded_recipe_images/'),
        ),
    ]
