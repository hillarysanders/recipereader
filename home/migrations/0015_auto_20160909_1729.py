# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-10 00:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_auto_20160909_1439'),
    ]

    operations = [
        migrations.CreateModel(
            name='ingredient_line',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_text', models.TextField(max_length=4096)),
            ],
        ),
        migrations.AddField(
            model_name='recipe',
            name='ingredients',
            field=models.TextField(blank=True, default='', max_length=4096, null=True),
        ),
        migrations.AddField(
            model_name='recipe',
            name='instructions',
            field=models.TextField(blank=True, default='', max_length=8192, null=True),
        ),
    ]
