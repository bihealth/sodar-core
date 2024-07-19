"""Test for UI view permissions in example_project_app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import ProjectPermissionTestBase
from projectroles.tests.test_models import AppSettingMixin

# Filesfolders dependency
from filesfolders.tests.test_models import FolderMixin


class TestExampleView(FolderMixin, AppSettingMixin, ProjectPermissionTestBase):
    """Permission tests for ExampleView"""

    def test_get(self):
        """Test ExampleView GET"""
        url = reverse(
            'example_project_app:example',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,  # Inherited
            self.user_delegate_cat,  # Inherited
            self.user_contributor_cat,  # Inherited
            self.user_guest_cat,  # Inherited
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        url = reverse(
            'example_project_app:example',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.assert_response(url, self.anonymous, 302)

    def test_get_ext_model(self):
        """Test GET with model from another app"""
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
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_ext_model_anon(self):
        """Test GET with model from another app and anonymous access"""
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
        self.assert_response(url, self.anonymous, 302)
