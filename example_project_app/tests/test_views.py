"""UI view tests for example_project_app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import ProjectMixin, RoleAssignmentMixin
from projectroles.tests.test_views import TestViewsBase

# Filesfolders dependency
from filesfolders.tests.test_models import FolderMixin


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestExampleView(
    FolderMixin, ProjectMixin, RoleAssignmentMixin, TestViewsBase
):
    """Tests for the example view"""

    def setUp(self):
        super().setUp()
        self.project = self._make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

    def test_render_project(self):
        """Test rendering of example view with a project kwarg"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'example_project_app:example',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)

    def test_render_ext_model(self):
        """Test rendering of example view with model from another app"""
        # Create object from filesfolders app model
        folder = self._make_folder(
            name='TestFolder',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'example_project_app:example_ext_model',
                    kwargs={'filesfolders__folder': folder.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
