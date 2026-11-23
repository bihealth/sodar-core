"""Tests for UI view permissions in the userprofile app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.base import SiteAppPermissionTestBase
from projectroles.tests.test_models import (
    SODARUserAdditionalEmailMixin,
    ADD_EMAIL,
)


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']


class TestUserDetailView(SiteAppPermissionTestBase):
    """Tests for UserDetailView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('userprofile:detail')

    def test_get_profile(self):
        """Test UserDetailView GET"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_profile_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_profile_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)


class TesUserSettingUpdateView(SiteAppPermissionTestBase):
    """Tests for UserSettingUpdateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('userprofile:settings_update')

    def test_get(self):
        """Test UserSettingUpdateView GET"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 302)


class TesUserEmailCreateView(SiteAppPermissionTestBase):
    """Tests for UserEmailCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('userprofile:email_create')

    def test_get(self):
        """Test UserEmailCreateView GET"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_target(self):
        """Test GET as target site"""
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 302)


class TesUserEmailDeleteView(
    SODARUserAdditionalEmailMixin, SiteAppPermissionTestBase
):
    """Tests for UserEmailDeleteView permissions"""

    def setUp(self):
        super().setUp()
        self.regular_user2 = self.make_user('regular_user2')
        self.email = self.make_email(self.regular_user, ADD_EMAIL)
        self.url = reverse(
            'userprofile:email_delete',
            kwargs={'sodaruseradditionalemail': self.email.sodar_uuid},
        )

    def test_get_email_delete(self):
        """Test UserEmailDeleteView GET"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(
            self.url, [self.regular_user2, self.anonymous], 302
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_email_delete_anon(self):
        """Test UserEmailDeleteView GET with anonymous access"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(
            self.url, [self.regular_user2, self.anonymous], 302
        )

    def test_get_email_delete_read_only(self):
        """Test UserEmailDeleteView GET with site read-only mode"""
        self.set_site_read_only()
        bad_users = [self.regular_user, self.regular_user2, self.anonymous]
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_email_delete_target(self):
        """Test UserEmailDeleteView GET as target site"""
        self.assert_response(self.url, [self.superuser], 200)
        self.assert_response(
            self.url,
            [self.regular_user, self.regular_user2, self.anonymous],
            302,
        )


class TestUserListView(SiteAppPermissionTestBase):
    """Tests for UserListView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('userprofile:list')

    def test_get(self):
        """Test UserListView GET"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_target(self):
        """Test GET as target site"""
        self.assert_response(self.url, [self.superuser, self.regular_user], 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_USER_LIST_ENABLE=False)
    def test_get_disable(self):
        """Test GET with user list view disabled"""
        self.assert_response(self.url, [self.superuser], 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 302)

    @override_settings(PROJECTROLES_API_USER_DETAIL_RESTRICT=True)
    def test_get_restrict(self):
        """Test GET with user list view role restriction"""
        self.init_roles()
        user_role = self.make_user('user_role')
        cat = self.make_project('TestCategory', PROJECT_TYPE_CATEGORY, None)
        self.make_assignment(cat, user_role, self.role_contributor)
        self.assert_response(self.url, [self.superuser, user_role], 200)
        self.assert_response(self.url, [self.regular_user, self.anonymous], 302)
