# Generated by Django 4.2.22 on 2025-06-19 10:44

from django.db import migrations


PROJECT_TYPE_PROJECT = 'PROJECT'
ROLE_NAME_GUEST = 'project guest'


def populate_public_access(apps, schema_editor):
    """Populate Project.public_access with former public_guest access values"""
    Project = apps.get_model('projectroles', 'Project')
    Role = apps.get_model('projectroles', 'Role')
    role_guest = Role.objects.get(name=ROLE_NAME_GUEST)
    for p in Project.objects.filter(type=PROJECT_TYPE_PROJECT):
        if p.public_guest_access:
            p.public_access = role_guest
            p.save()


def revert_public_access(apps, schema_editor):
    """Revert Project.public_access populating"""
    Project = apps.get_model('projectroles', 'Project')
    for p in Project.objects.filter(type=PROJECT_TYPE_PROJECT):
        if p.public_access:
            p.public_access = None
            p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0036_project_public_access'),
    ]
    operations = [
        migrations.RunPython(
            code=populate_public_access,
            reverse_code=revert_public_access,
        ),
    ]
