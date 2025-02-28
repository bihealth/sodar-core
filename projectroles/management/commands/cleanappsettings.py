"""
Cleanappsettings management command for cleaning up undefined or orphaned app
settings.
"""

from django.core.management.base import BaseCommand

from projectroles.app_settings import AppSettingAPI
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import AppSetting, SODAR_CONSTANTS


app_settings = AppSettingAPI()
logger = ManagementCommandLogger(__name__)

# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local constants
APP_NAME = 'projectroles'
START_MSG = 'Querying database for undefined app settings..'
CHECK_MODE_MSG = 'Check mode enabled, database will not be altered'
END_MSG = 'OK'
DEF_NOT_FOUND_MSG = 'definition not found'
ALLOWED_TYPES_MSG = 'does not match allowed types'
LOG_NONE_LABEL = 'None'
PREFIX_MSG = '"{s_name}" (project={project}; user={user}): '
CHECK_PREFIX_MSG = 'Found ' + PREFIX_MSG
DELETE_PREFIX_MSG = 'Deleting ' + PREFIX_MSG
DELETE_PROJECT_TYPE_MSG = 'project type "{}" {}: {}'
DELETE_SCOPE_MSG = 'user has no role in project'


class Command(BaseCommand):
    """Command for cleaning up undefined or orphaned app settings"""

    help = (
        'Cleans up undefined or otherwise orphaned app settings from the '
        'database.'
    )

    @classmethod
    def _get_log_msg(cls, s, msg, check):
        """Return delete/check message for logging"""
        prefix_msg = CHECK_PREFIX_MSG if check else DELETE_PREFIX_MSG
        s_name = '.'.join(
            [
                'settings',
                APP_NAME if s.app_plugin is None else s.app_plugin.name,
                s.name,
            ]
        )
        p_str = f'"{s.project.title}"' if s.project else LOG_NONE_LABEL
        u_str = f'"{s.user.username}"' if s.user else LOG_NONE_LABEL
        return prefix_msg.format(s_name=s_name, project=p_str, user=u_str) + msg

    def add_arguments(self, parser):
        parser.add_argument(
            '-c',
            '--check',
            dest='check',
            required=False,
            default=False,
            action='store_true',
            help='Log settings to be cleaned up without altering the database',
        )

    def handle(self, *args, **options):
        check = options.get('check', False)
        if check:
            logger.info(CHECK_MODE_MSG)
        logger.info(START_MSG)
        s_def = None
        p_types = []
        db_settings = AppSetting.objects.all()
        for s in db_settings:
            # Undefined settings
            def_kwargs = {'name': s.name}
            if s.app_plugin:
                def_kwargs['plugin'] = s.app_plugin.get_plugin()
            else:
                def_kwargs['plugin_name'] = APP_NAME
            try:
                s_def = app_settings.get_definition(**def_kwargs)
                # Get allowed project types (if unset, default is PROJECT only)
                if s_def.scope != APP_SETTING_SCOPE_USER:
                    p_types = s_def.project_types
            except ValueError:
                logger.info(self._get_log_msg(s, DEF_NOT_FOUND_MSG, check))
                if not check:
                    s.delete()
                    continue
            # Invalid scope
            if s_def and s.project and s.project.type not in p_types:
                msg = DELETE_PROJECT_TYPE_MSG.format(
                    s.project.type, ALLOWED_TYPES_MSG, ', '.join(p_types)
                )
                logger.info(self._get_log_msg(s, msg, check))
                if not check:
                    s.delete()
                    continue
            # No user role for PROJECT_USER scope setting
            if s.project and s.user and not s.project.get_role(s.user):
                logger.info(self._get_log_msg(s, DELETE_SCOPE_MSG, check))
                if not check:
                    s.delete()
        logger.info(END_MSG)
