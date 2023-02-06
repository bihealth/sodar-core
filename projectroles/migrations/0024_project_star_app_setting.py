from django.db import migrations, models
from projectroles.app_settings import AppSettingAPI


def set_ranks(apps, schema_editor):
    """Set rank values for existing roles"""
    UserTag = apps.get_model('projectroles', 'ProjectUserTag')
    Project = apps.get_model('projectroles', 'Project')
    app_settings = AppSettingAPI()
    for project in Project.objects.all():
        user_tag = UserTag.objects.filter(project=project)
        if user_tag is not None:
            app_settings.set(
                app_name='projectroles',
                setting_name='project_star',
                value=True,
                project=project,
                user=user_tag.user,
                validate=False,
            )


class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0023_project_archive'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='rank',
            field=models.IntegerField(default=0, help_text='Role rank for determining role hierarchy'),
        ),
        migrations.RunPython(set_ranks, reverse_code=migrations.RunPython.noop)
        # migrations.DeleteModel(
        #     name='ProjectUserTag',
        # ),
    ]
