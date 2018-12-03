# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-12-03 04:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('athenatools', '0007_auto_20181130_0853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='title',
            field=models.CharField(db_index=True, max_length=255, verbose_name=b'\xe5\x90\x8d\xe7\xa7\xb0'),
        ),
        migrations.AlterField(
            model_name='purchase',
            name='day',
            field=models.DateField(blank=True, db_index=True, default=django.utils.timezone.localdate, null=True, verbose_name=b'\xe6\x97\xa5\xe6\x9c\x9f'),
        ),
    ]
