from django.core.management.base import BaseCommand

from projectroles.app_settings import AppSettingAPI
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import AppSetting


app_settings = AppSettingAPI()
logger = ManagementCommandLogger(__name__)


# Local constants
START_MSG = 'Checking database for undefined app settings..'
END_MSG = 'OK'


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
                if s.project and s.project.type not in definition.get(
                    'project_types', ['PROJECT']
                ):
                    logger.info(
                        'Deleting "{}" from project "{}" - project type "{}" does not match allowed types: {}'.format(
                            get_setting_str(s),
                            s.project.title,
                            s.project.type,
                            definition.get('project_types', []),
                        )
                    )
                    s.delete()
                elif not definition:
                    logger.info(
                        'Deleting "{}" from project "{}" - definition not found'.format(
                            get_setting_str(s), s.project.title
                        )
                    )
                    s.delete()
            except ValueError:
                logger.info(
                    'Deleting "{}" from project "{}" - definition not found'.format(
                        get_setting_str(s), s.project.title
                    )
                )
                s.delete()
        logger.info(END_MSG)
