# Generated by Django 3.2.17 on 2023-02-02 13:13

from django.db import migrations
import uuid


def gen_uuid(apps, schema_editor):
    ProjectEventStatus = apps.get_model('timeline', 'ProjectEventStatus')
    for status in ProjectEventStatus.objects.all():
        status.sodar_uuid = uuid.uuid4()
        status.save(update_fields=['sodar_uuid'])

class Migration(migrations.Migration):

    dependencies = [
        ('timeline', '0009_create_status_uuid'),
    ]

    operations = [
        migrations.RunPython(gen_uuid, reverse_code=migrations.RunPython.noop)
    ]
