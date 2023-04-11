from test_plus.test import TestCase

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    SODAR_CONSTANTS,
)
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.tasks import sync_remote_site_task
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RemoteTargetMixin,
)


app_settings = AppSettingAPI()
remote_projects = RemoteProjectAPI()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']


class TestSyncRemoteSiteTask(
    TestCase, ProjectMixin, RoleMixin, RemoteTargetMixin
):
    """Tests for the sync_remote_site_task() task"""

    def setUp(self):
        super().setUp()
        self.user = self.make_user('user')
        self.category = self.make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.project = self.make_project(
            'test_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.source_site, self.remote_projects = self.set_up_as_target(
            projects=[self.category, self.project]
        )

    def test_sync_remote_site_task(self):
        """Test sync_remote_site_task()"""
        self.assertEqual(Project.objects.count(), 2)

        sync_remote_site_task()
