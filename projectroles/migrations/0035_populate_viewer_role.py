# Generated by Django 4.2.22 on 2025-06-10 12:18

from django.db import migrations


ROLE_NAME = 'project viewer'
ROLE_RANK = 45
ROLE_DESC = (
    'The project viewer role is a limited guest role. They can view general '
    'project details and its members, but they can not access all apps, data '
    'or files in the project.'
)


def populate_viewer_role(apps, schema_editor):
    """Populate Role object for viewer role"""
    Role = apps.get_model('projectroles', 'Role')
    Role.objects.create(name=ROLE_NAME, rank=ROLE_RANK, description=ROLE_DESC)


def revert_viewer_role(apps, schema_editor):
    """Revert Role object creation for viewer role"""
    Role = apps.get_model('projectroles', 'Role')
    viewer_role = Role.objects.filter(name=ROLE_NAME).first()
    if viewer_role:
        viewer_role.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0034_fix_project_star'),
    ]
    operations = [
        migrations.RunPython(
            code=populate_viewer_role,
            reverse_code=revert_viewer_role,
        ),
    ]
