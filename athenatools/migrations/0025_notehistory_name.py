# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-06-15 15:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('athenatools', '0024_notehistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='notehistory',
            name='name',
            field=models.CharField(blank=True, default=b'\xe8\x87\xaa\xe5\x8a\xa8\xe4\xbf\x9d\xe5\xad\x98', max_length=100),
        ),
    ]
