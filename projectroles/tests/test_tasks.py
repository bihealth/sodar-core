"""Tests for tasks in the projectroles app"""

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Role,
    SODAR_CONSTANTS,
    ROLE_RANKING,
    RemoteSite,
    RemoteProject,
)
from projectroles.tasks import sync_remote_site_task
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RemoteTargetMixin,
    RoleAssignmentMixin,
)


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']

# Local constants
APP_NAME = 'projectroles'


class TestSyncRemoteSiteTask(
    ProjectMixin, RoleMixin, RemoteTargetMixin, RoleAssignmentMixin, TestCase
):
    """Tests for the sync_remote_site_task() task"""

    maxDiff = None

    def setUp(self):
        super().setUp()
        self.role_owner = Role.objects.get_or_create(
            name=PROJECT_ROLE_OWNER, rank=ROLE_RANKING[PROJECT_ROLE_OWNER]
        )[0]
        self.user = self.make_user('user')
        self.user.save()
        self.category = self.make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(self.category, self.user, self.role_owner)
        self.project_source = self.make_project(
            'test_project_source', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as_source = self.make_assignment(
            self.project_source, self.user, self.role_owner
        )
        self.project_target = self.make_project(
            'test_project_target', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as_target = self.make_assignment(
            self.project_target, self.user, self.role_owner
        )
        self.source_site, self.remote_projects = self.set_up_as_target(
            projects=[self.category, self.project_source]
        )

    def test_sync_task(self):
        """Test sync_remote_site_task()"""
        sync_remote_site_task()

        self.assertEqual(RemoteSite.objects.all().count(), 1)
        self.assertEqual(RemoteSite.objects.first().name, self.source_site.name)
        self.assertEqual(RemoteProject.objects.all().count(), 2)

    def test_sync_change_name_task(self):
        """Test sync_remote_site_task() after title change in source site"""
        sync_remote_site_task()
        self.project_source.title = 'new title'
        self.project_source.save()
        sync_remote_site_task()

        self.assertEqual(RemoteSite.objects.all().count(), 1)
        self.assertEqual(RemoteSite.objects.first().name, self.source_site.name)
        self.assertEqual(RemoteProject.objects.all().count(), 2)
        self.assertEqual(
            RemoteProject.objects.get(
                project=self.project_source
            ).project.title,
            'new title',
        )

    def test_sync_change_settings_task(self):
        """
        Test sync_remote_site_task() after app_settings changes in source site.
        """
        sync_remote_site_task()
        app_settings.set(
            APP_NAME, 'ip_restrict', True, project=self.project_source
        )
        sync_remote_site_task()

        self.assertEqual(RemoteSite.objects.all().count(), 1)
        self.assertEqual(RemoteSite.objects.first().name, self.source_site.name)
        self.assertEqual(RemoteProject.objects.all().count(), 2)
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'ip_restrict', project=self.project_source
            ),
            True,
        )
