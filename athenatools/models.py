# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone


class Reminder(models.Model):

    METHOD_CHOICES = (
        (1, 'Email'),
        (2, 'SMS'),
    )
    name = models.CharField(max_length=255, blank=True)
    method = models.IntegerField(choices=METHOD_CHOICES, default=1)
    ahead_hours = models.IntegerField(default=24)
    enable = models.BooleanField(default=True)
    update_time = models.DateTimeField(auto_now=True)
    create_time = models.DateTimeField(default=timezone.now)
