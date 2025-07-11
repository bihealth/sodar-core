# Generated by Django 4.2.23 on 2025-07-01 15:11

from django.db import migrations


def update_ip_allow_list(apps, schema_editor):
    """
    Update IP allow list settings for new setting definition, delete old setting
    objects.
    """
    AppSetting = apps.get_model('projectroles', 'AppSetting')
    for s in AppSetting.objects.filter(name='ip_allowlist'):
        if s.value_json and isinstance(s.value_json, list):
            try:
                AppSetting.objects.create(
                    app_plugin=None,
                    project=s.project,
                    user=None,
                    name='ip_allow_list',
                    type='STRING',
                    value=','.join(s.value_json),
                    value_json=None,
                    user_modifiable=True,
                )
            except Exception:
                pass
        s.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0037_populate_public_access'),
    ]

    operations = [
        migrations.RunPython(
            code=update_ip_allow_list,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
