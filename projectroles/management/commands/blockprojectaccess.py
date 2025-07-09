"""
Blockprojectaccess management command for temporarily blocking or unblocking
user access to a project.
"""

import sys

from django.core.management.base import BaseCommand

from projectroles.app_settings import AppSettingAPI
from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import Project


app_settings = AppSettingAPI()
logger = ManagementCommandLogger(__name__)


# Local constants
APP_NAME = 'projectroles'
SET_NAME = 'project_access_block'
PROJECT_NOT_FOUND_MSG = 'Project not found with UUID: {project_uuid}'
INVALID_PROJECT_TYPE_MSG = 'This action only supports projects of PROJECT type'
MODE_CONVERT_ERR_MSG = 'Exception converting mode "{mode}": {ex}'
INVALID_MODE_MSG = 'Invalid mode: {mode} (accepted: 0, 1)'


class Command(BaseCommand):
    """Command for cleaning up undefined or orphaned app settings"""

    help = (
        'Toggle temporary project access block. When enabled, this prevents '
        'access to all views to the given project for non-superusers.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--project',
            dest='project',
            required=True,
            action='store',
            help='UUID of project to be blocked or unblocked',
        )
        parser.add_argument(
            '-m',
            '--mode',
            dest='mode',
            required=True,
            action='store',
            help='Mode to be set (1=blocked, 0=unblocked)',
        )

    def handle(self, *args, **options):
        p_uuid = options.get('project')
        project = Project.objects.filter(sodar_uuid=p_uuid).first()
        if not project:
            logger.error(PROJECT_NOT_FOUND_MSG.format(project_uuid=p_uuid))
            sys.exit(1)
        if project.is_category():
            logger.error(INVALID_PROJECT_TYPE_MSG)
            sys.exit(1)
        try:
            mode = int(options.get('mode'))
        except Exception as ex:
            logger.error(
                MODE_CONVERT_ERR_MSG.format(mode=options.get('mode'), ex=ex)
            )
            sys.exit(1)
        if mode not in [0, 1]:
            logger.error(INVALID_MODE_MSG.format(mode=mode))
            sys.exit(1)
        old_val = app_settings.get(APP_NAME, SET_NAME, project=project)
        logger.debug(f'Previous mode: {int(old_val)}')
        app_settings.set(APP_NAME, SET_NAME, value=bool(mode), project=project)
        action = 'enabled' if mode else 'disabled'
        logger.info(f'Project access block {action}: {project.get_log_title()}')
