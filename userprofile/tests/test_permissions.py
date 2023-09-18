"""Tests for UI view permissions in the userprofile app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestSiteAppPermissionBase


class TestUserProfilePermissions(TestSiteAppPermissionBase):
    """Tests for userprofile view permissions"""

    def test_get_profile(self):
        """Test UserDetailView GET"""
        url = reverse('userprofile:detail')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_profile_anon(self):
        """Test UserDetailView GET with anonymous access"""
        url = reverse('userprofile:detail')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_settings_update(self):
        """Test UserSettingUpdateView GET"""
        url = reverse('userprofile:settings_update')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_settings_update_anon(self):
        """Test UserSettingUpdateView GET with anonymous access"""
        url = reverse('userprofile:settings_update')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)
