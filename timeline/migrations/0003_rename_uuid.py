# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-19 15:15
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0002_projectevent_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projectevent',
            old_name='omics_uuid',
            new_name='sodar_uuid'
        ),
    ]