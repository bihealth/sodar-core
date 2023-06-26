"""
Syncmodifyapi management command for synchronizing existing projects using the
project modify API
"""

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
        sync_count = 0
        err_count = 0
        for p in project_list:
            p_title = p.get_log_title(full_title=True)
            logger.debug('Synchronizing project: {}'.format(p_title))
            try:
                self.call_project_modify_api('perform_project_sync', None, [p])
                sync_count += 1
            except Exception as ex:
                logger.error(
                    'Exception in project sync for project {}: {}'.format(
                        p_title, ex
                    )
                )
                err_count += 1
        logger.info(
            'Project data synchronized ({} OK, {} error{})'.format(
                sync_count, err_count, 's' if err_count != 1 else ''
            )
        )
