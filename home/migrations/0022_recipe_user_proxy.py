# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-21 05:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0021_userproxy'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='user_proxy',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='home.UserProxy'),
        ),
    ]
