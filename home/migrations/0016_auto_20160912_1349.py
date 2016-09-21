# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-12 20:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0015_auto_20160909_1729'),
    ]

    operations = [
        migrations.CreateModel(
            name='IngredientLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_text', models.TextField(max_length=4096)),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.Recipe')),
            ],
        ),
        migrations.DeleteModel(
            name='ingredient_line',
        ),
    ]