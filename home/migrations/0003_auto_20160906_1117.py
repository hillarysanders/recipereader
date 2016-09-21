# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-06 18:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_auto_20160902_2032'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headline', models.CharField(max_length=50)),
                ('content', models.CharField(max_length=1024)),
            ],
        ),
        migrations.RemoveField(
            model_name='recipe',
            name='pub_date',
        ),
        migrations.RemoveField(
            model_name='recipe',
            name='user',
        ),
        migrations.AlterField(
            model_name='recipe',
            name='ingredients_text',
            field=models.TextField(max_length=2048),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='instructions_text',
            field=models.TextField(max_length=2048),
        ),
    ]