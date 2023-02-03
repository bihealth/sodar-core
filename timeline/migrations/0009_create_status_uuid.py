# Generated by Django 3.2.17 on 2023-02-02 13:12

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0008_projectevent_plugin'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecteventstatus',
            name='sodar_uuid',
            field=models.UUIDField(default=uuid.uuid4, help_text='Status SODAR UUID', null=True),
        ),
    ]
