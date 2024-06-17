# Generated by Django 4.2.11 on 2024-06-11 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projectroles", "0030_populate_sodaruseradditionalemail"),
    ]

    operations = [
        migrations.AddField(
            model_name="remotesite",
            name="owner_modifiable",
            field=models.BooleanField(
                default=True,
                help_text="Allow owners and delegates to modify project access for this site",
            ),
        ),
        migrations.AlterField(
            model_name="remotesite",
            name="user_display",
            field=models.BooleanField(default=True, help_text="Display site to users"),
        ),
    ]
