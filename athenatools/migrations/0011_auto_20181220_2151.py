# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-12-20 13:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('athenatools', '0010_auto_20181212_1750'),
    ]

    operations = [
        migrations.RenameField(
            model_name='purchase',
            old_name='remark',
            new_name='group',
        ),
    ]