from django.db import migrations


def migrate_stars(apps, schema_editor):
    """Set rank values for existing roles"""
    ProjectUserTag = apps.get_model('projectroles', 'ProjectUserTag')
    Project = apps.get_model('projectroles', 'Project')
    AppSetting = apps.get_model('projectroles', 'AppSetting')
    for project in Project.objects.all():
        user_tag = ProjectUserTag.objects.filter(project=project).first()
        if user_tag is not None:
            setting = AppSetting()
            setting.project = project
            setting.user = user_tag.user
            setting.value = True
            setting.name = 'project_star'
            setting.user_modifiable = True
            setting.save()


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
