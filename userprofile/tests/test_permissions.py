"""Tests for permissions in the userprofile app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestSiteAppPermissionBase


class TestUserProfilePermissions(TestSiteAppPermissionBase):
    """Tests for userprofile view permissions"""

    def test_profile(self):
        """Test permissions for user profile view"""
        url = reverse('userprofile:detail')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_profile_anon(self):
        """Test permissions for user profile view with anonymous access"""
        url = reverse('userprofile:detail')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_settings_update(self):
        """Test permissions for user settings update view"""
        url = reverse('userprofile:settings_update')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_settings_update_anon(self):
        """Test permissions for update view with anonymous access"""
        url = reverse('userprofile:settings_update')
        good_users = [self.superuser, self.regular_user]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
