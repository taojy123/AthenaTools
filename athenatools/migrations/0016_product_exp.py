# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-03-03 05:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('athenatools', '0015_auto_20190115_1446'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='exp',
            field=models.CharField(blank=True, max_length=255, verbose_name=b'\xe9\xbb\x98\xe8\xae\xa4\xe4\xbf\x9d\xe8\xb4\xa8\xe6\x9c\x9f'),
        ),
    ]
