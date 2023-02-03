"""UI view permission tests for example_project_app"""

from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestProjectPermissionBase
from projectroles.tests.test_models import AppSettingMixin

# Filesfolders dependency
from filesfolders.tests.test_models import FolderMixin


class TestExampleViews(FolderMixin, AppSettingMixin, TestProjectPermissionBase):
    """Permission tests for example UI views"""

    def test_example_project(self):
        """Test permissions for example view with project"""
        url = reverse(
            'example_project_app:example',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,  # Inherited
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)

    def test_example_ext_model(self):
        """Test permissions for example view with model from another app"""
        # Create object from filesfolders app model
        folder = self.make_folder(
            name='TestFolder',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        url = reverse(
            'example_project_app:example_ext_model',
            kwargs={'filesfolders__folder': folder.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,  # Inherited
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)
