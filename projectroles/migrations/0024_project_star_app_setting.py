from django.db import migrations
from projectroles.app_settings import AppSettingAPI
from projectroles.models import Project, ProjectUserTag

app_settings = AppSettingAPI()

def migrate_stars(apps, schema_editor):
    """Set rank values for existing roles"""
    # UserTag = apps.get_model('projectroles', 'ProjectUserTag')
    # Project = apps.get_model('projectroles', 'Project')
    for project in Project.objects.all():
        # project = Project.objects.filter(
        #         sodar_uuid=pr.sodar_uuid
        #     ).first()
        user_tag = ProjectUserTag.objects.filter(project=project).first()
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
        migrations.RunPython(migrate_stars, reverse_code=migrations.RunPython.noop)
        # migrations.DeleteModel(
        #     name='ProjectUserTag',
        # ),
    ]
