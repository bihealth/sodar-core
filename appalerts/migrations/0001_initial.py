# Generated by Django 3.1.8 on 2021-04-16 12:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('djangoplugins', '0001_initial'),
        ('projectroles', '0019_project_public_guest_access'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_name', models.CharField(help_text='Internal alert name string', max_length=255)),
                ('message', models.TextField(help_text='Alert message (may contain HTML)')),
                ('level', models.CharField(choices=[('INFO', 'Info'), ('SUCCESS', 'Success'), ('WARNING', 'Warning'), ('DANGER', 'Danger')], default='INFO', help_text='Alert level', max_length=64)),
                ('active', models.BooleanField(default=True, help_text='Active status of the alert')),
                ('url', models.URLField(blank=True, help_text='URL for the source of the alert (optional)', max_length=2000, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='DateTime of the alert creation')),
                ('sodar_uuid', models.UUIDField(default=uuid.uuid4, help_text='Alert SODAR UUID', unique=True)),
                ('app_plugin', models.ForeignKey(help_text='App to which the alert belongs', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='app_alerts', to='djangoplugins.plugin')),
                ('project', models.ForeignKey(help_text='Project to which the alert belongs (optional)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='app_alerts', to='projectroles.project')),
                ('user', models.ForeignKey(help_text='User who receives the alert', on_delete=django.db.models.deletion.CASCADE, related_name='app_alerts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
