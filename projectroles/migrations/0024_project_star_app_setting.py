from django.db import migrations


def migrate_stars(apps, schema_editor):
    """Create project_star AppSettings"""
    ProjectUserTag = apps.get_model('projectroles', 'ProjectUserTag')
    AppSetting = apps.get_model('projectroles', 'AppSetting')
    for projectusertag in ProjectUserTag.objects.all():
        AppSetting.objects.get_or_create(
            project=projectusertag.project,
            user=projectusertag.user,
            value=True,
            name='project_star',
        )



class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0023_project_archive'),
    ]

    operations = [
        migrations.RunPython(migrate_stars, reverse_code=migrations.RunPython.noop)
        # migrations.DeleteModel(
        #     name='ProjectUserTag',
        # ),
    ]
