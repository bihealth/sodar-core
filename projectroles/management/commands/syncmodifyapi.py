"""
Syncmodifyapi management command for synchronizing existing projects using the
project modify API.
"""

import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from projectroles.management.logging import ManagementCommandLogger
from projectroles.models import Project, SODAR_CONSTANTS
from projectroles.views import ProjectModifyPluginViewMixin


logger = ManagementCommandLogger(__name__)
User = get_user_model()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']


class Command(ProjectModifyPluginViewMixin, BaseCommand):
    help = 'Synchronizes existing projects using the project modify API'

    def add_arguments(self, parser):
        parser.add_argument(
            '-p',
            '--project',
            metavar='UUID',
            type=str,
            help='Limit sync to a project',
        )

    def handle(self, *args, **options):
        """Run management command"""
        project_uuid = options.get('project')
        if project_uuid:
            logger.info(
                f'Limiting sync to project with UUID "{project_uuid}"..'
            )
            project = Project.objects.filter(sodar_uuid=project_uuid).first()
            if not project:
                logger.error('Project not found')
                sys.exit(1)
            project_list = [project]
        else:
            logger.info('Synchronizing all projects..')
            project_list = Project.objects.all().order_by('full_title')
            logger.debug(
                f'Found {project_list.count()} projects and categories'
            )
        sync_count = 0
        err_count = 0
        for p in project_list:
            p_title = p.get_log_title(full_title=True)
            logger.debug(f'Synchronizing project {p_title}')
            try:
                self.call_project_modify_api('perform_project_sync', None, [p])
                sync_count += 1
            except Exception as ex:
                logger.error(f'Exception for project {p_title}: {ex}')
                err_count += 1
        logger.info(
            'Project data synchronized ({} OK, {} error{})'.format(
                sync_count, err_count, 's' if err_count != 1 else ''
            )
        )
