"""Tests for UI view permissions in the userprofile app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import (
    SODARUserAdditionalEmailMixin,
    ADD_EMAIL,
)
from projectroles.tests.test_permissions import SiteAppPermissionTestBase


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']


class TestUserProfilePermissions(
    SODARUserAdditionalEmailMixin, SiteAppPermissionTestBase
):
    """Tests for userprofile view permissions"""

    def setUp(self):
        super().setUp()
        self.regular_user2 = self.make_user('regular_user2')

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

    def test_get_profile_read_only(self):
        """Test UserDetailView GET with site read-only mode"""
        self.set_site_read_only()
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

    def test_get_settings_update_read_only(self):
        """Test UserSettingUpdateView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('userprofile:settings_update')
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, [self.regular_user, self.anonymous], 302)

    def test_get_email_create(self):
        """Test UserEmailCreateView GET"""
        url = reverse('userprofile:email_create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_email_create_anon(self):
        """Test UserEmailCreateView GET with anonymous access"""
        url = reverse('userprofile:email_create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_email_create_read_only(self):
        """Test UserEmailCreateView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('userprofile:email_create')
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, [self.regular_user, self.anonymous], 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_email_create_target(self):
        """Test UserEmailCreateView GET as target site"""
        url = reverse('userprofile:email_create')
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, [self.regular_user, self.anonymous], 302)

    def test_get_email_delete(self):
        """Test UserEmailDeleteView GET"""
        email = self.make_email(self.regular_user, ADD_EMAIL)
        url = reverse(
            'userprofile:email_delete',
            kwargs={'sodaruseradditionalemail': email.sodar_uuid},
        )
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, [self.regular_user2, self.anonymous], 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_email_delete_anon(self):
        """Test UserEmailDeleteView GET with anonymous access"""
        email = self.make_email(self.regular_user, ADD_EMAIL)
        url = reverse(
            'userprofile:email_delete',
            kwargs={'sodaruseradditionalemail': email.sodar_uuid},
        )
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, [self.regular_user2, self.anonymous], 302)

    def test_get_email_delete_read_only(self):
        """Test UserEmailDeleteView GET with site read-only mode"""
        self.set_site_read_only()
        email = self.make_email(self.regular_user, ADD_EMAIL)
        url = reverse(
            'userprofile:email_delete',
            kwargs={'sodaruseradditionalemail': email.sodar_uuid},
        )
        bad_users = [self.regular_user, self.regular_user2, self.anonymous]
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_email_delete_target(self):
        """Test UserEmailDeleteView GET as target site"""
        email = self.make_email(self.regular_user, ADD_EMAIL)
        url = reverse(
            'userprofile:email_delete',
            kwargs={'sodaruseradditionalemail': email.sodar_uuid},
        )
        self.assert_response(url, [self.superuser], 200)
        self.assert_response(
            url, [self.regular_user, self.regular_user2, self.anonymous], 302
        )
