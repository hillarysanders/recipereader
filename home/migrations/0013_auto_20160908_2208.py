# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-09 05:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_auto_20160908_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cook_time_hours',
            field=models.IntegerField(blank=True, null=True, verbose_name='Cook time'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cook_time_minutes',
            field=models.IntegerField(blank=True, null=True, verbose_name=''),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients_text',
            field=models.TextField(max_length=4096),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='instructions_text',
            field=models.TextField(max_length=8192),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='num_servings',
            field=models.IntegerField(blank=True, default=4),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='prep_time_hours',
            field=models.IntegerField(blank=True, null=True, verbose_name='Prep time'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='prep_time_minutes',
            field=models.IntegerField(blank=True, null=True, verbose_name=''),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ready_in_hours',
            field=models.IntegerField(blank=True, null=True, verbose_name='Ready in'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ready_in_minutes',
            field=models.IntegerField(blank=True, null=True, verbose_name=''),
        ),
    ]
