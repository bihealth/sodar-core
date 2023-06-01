from django.db import migrations

from projectroles.models import PROJECT_TAG_STARRED


def migrate_stars(apps, schema_editor):
    """Create project_star AppSettings"""
    ProjectUserTag = apps.get_model('projectroles', 'ProjectUserTag')
    AppSetting = apps.get_model('projectroles', 'AppSetting')
    for tag in ProjectUserTag.objects.filter(name=PROJECT_TAG_STARRED):
        AppSetting.objects.get_or_create(
            project=tag.project,
            user=tag.user,
            value=True,
            name='project_star',
        )


class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0023_project_archive'),
    ]

    operations = [
        migrations.RunPython(migrate_stars, reverse_code=migrations.RunPython.noop),
    ]
