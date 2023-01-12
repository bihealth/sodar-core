# Generated by Django 3.2.16 on 2023-01-10 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projectroles', '0022_role_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='archive',
            field=models.BooleanField(default=False, help_text='Project is archived (read-only)'),
        ),
    ]