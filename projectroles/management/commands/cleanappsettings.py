"""
Cleanappsettings management command for cleaning up unused or invalid app
settings
"""

from django.core.management.base import BaseCommand

from projectroles.app_settings import AppSettingAPI
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import AppSetting


app_settings = AppSettingAPI()
logger = ManagementCommandLogger(__name__)


# Local constants
START_MSG = 'Checking database for undefined app settings..'
END_MSG = 'OK'
DEFINITION_NOT_FOUND_MSG = 'definition not found'
ALLOWED_TYPES_MSG = 'does not match allowed types'
DELETE_PREFIX_MSG = 'Deleting "{}" from project "{}": '
DELETE_PROJECT_TYPE_MSG = 'project type "{}" {}: {}'
DELETE_SCOPE_MSG = 'user {} has no role in project'


def get_setting_str(db_setting):
    return '.'.join(
        [
            'settings',
            'projectroles'
            if db_setting.app_plugin is None
            else db_setting.app_plugin.name,
            db_setting.name,
        ]
    )


class Command(BaseCommand):
    help = 'Cleans up undefined app settings from the database.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        logger.info(START_MSG)
        db_settings = AppSetting.objects.filter(user=None)
        for s in db_settings:
            def_kwargs = {'name': s.name}
            if s.app_plugin:
                def_kwargs['plugin'] = s.app_plugin.get_plugin()
            else:
                def_kwargs['app_name'] = 'projectroles'
            try:
                definition = app_settings.get_definition(**def_kwargs)
            except ValueError:
                logger.info(
                    DELETE_PREFIX_MSG.format(
                        get_setting_str(s), s.project.title
                    )
                    + DEFINITION_NOT_FOUND_MSG
                )
                s.delete()
                continue
            if s.project and s.project.type not in definition.get(
                'project_types', ['PROJECT']
            ):
                logger.info(
                    DELETE_PREFIX_MSG.format(
                        get_setting_str(s), s.project.title
                    )
                    + DELETE_PROJECT_TYPE_MSG.format(
                        s.project.type,
                        ALLOWED_TYPES_MSG,
                        definition.get('project_types', ['PROJECT']),
                    )
                )
                s.delete()

        db_settings = AppSetting.objects.filter(
            project__isnull=False, user__isnull=False
        )
        for s in db_settings:
            if not s.project.get_role(s.user):
                logger.info(
                    DELETE_PREFIX_MSG.format(
                        get_setting_str(s), s.project.title
                    )
                    + DELETE_SCOPE_MSG.format(s.user.username)
                )
                s.delete()
        logger.info(END_MSG)
