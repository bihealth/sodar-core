"""
Syncmodifyapi management command for synchronizing existing projects using the
project modify API
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

    def _get_projects(self, project, project_list):
        """
        Retrieve projects recursively in inheritance order.

        :param project: Current project
        :param project_list: List of Project objects
        """
        project_list.append(project)
        logger.debug('Added: {}'.format(project.full_title))
        for c in Project.objects.filter(parent=project):
            self._get_projects(c, project_list)
        return project_list

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        """Run management command"""
        logger.info('Synchronizing projects..')
        project_list = []
        top_cats = Project.objects.filter(
            type=PROJECT_TYPE_CATEGORY, parent=None
        )
        for c in top_cats:
            self._get_projects(c, project_list)
        logger.debug(
            'Found {} projects and categories'.format(len(project_list))
        )
        try:
            for p in project_list:
                logger.debug('Synchronizing project: {}'.format(p.full_title))
                self.call_project_modify_api('perform_project_sync', None, [p])
        except Exception as ex:
            logger.error('Exception in project sync: {}'.format(ex))
            logger.error('Project sync failed! Unable to continue, exiting..')
            sys.exit(1)
        logger.info('Project data synchronized.')
