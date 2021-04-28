# Generated by Django 3.1.7 on 2021-02-25 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0004_update_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectevent',
            name='extra_data',
            field=models.JSONField(default=dict, help_text='Additional event data as JSON'),
        ),
        migrations.AlterField(
            model_name='projecteventobjectref',
            name='extra_data',
            field=models.JSONField(default=dict, help_text='Additional data related to the object as JSON'),
        ),
        migrations.AlterField(
            model_name='projecteventstatus',
            name='extra_data',
            field=models.JSONField(default=dict, help_text='Additional status data as JSON'),
        ),
    ]
