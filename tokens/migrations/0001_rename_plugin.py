# Generated by Django 4.2.18 on 2025-02-04 09:39

from django.db import migrations


def rename_plugin(apps, schema_editor):
    Plugin = apps.get_model('djangoplugins', 'Plugin')
    plugin = Plugin.objects.filter(name='tokens').first()
    if plugin:
        plugin.pythonpath = 'tokens.plugins.SiteAppPlugin'
        plugin.save()


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.RunPython(
            code=rename_plugin,
            reverse_code=migrations.RunPython.noop,
        )
    ]
