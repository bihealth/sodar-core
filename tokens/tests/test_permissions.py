"""Tests for UI view permissions in the tokens app"""

from django.test import override_settings
from django.urls import reverse

from knox.models import AuthToken

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_permissions import SiteAppPermissionTestBase


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']


class TestTokenPermissions(SiteAppPermissionTestBase):
    """Tests for token view permissions"""

    def test_get_list(self):
        """Test UserTokenListView GET"""
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_list_anon(self):
        """Test UserTokenListView GET with anonymous access"""
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_list_read_only(self):
        """Test UserTokenListView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_create(self):
        """Test UserTokenCreateView GET"""
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_get_create_restrict(self):
        """Test UserTokenCreateView GET with restricted creation"""
        self.init_roles()
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.regular_user, self.role_guest)
        user_no_roles = self.make_user('user_no_roles')
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, [user_no_roles, self.anonymous], 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_create_anon(self):
        """Test UserTokenCreateView GET with anonymous access"""
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_create_read_only(self):
        """Test UserTokenCreateView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('tokens:create')
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, [self.regular_user, self.anonymous], 302)

    def test_get_delete(self):
        """Test UserTokenDeleteView GET"""
        token = AuthToken.objects.create(self.regular_user, None)
        url = reverse('tokens:delete', kwargs={'pk': token[0].pk})
        self.assert_response(url, self.regular_user, 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_delete_read_only(self):
        """Test UserTokenDeleteView GET with site read-only mode"""
        self.set_site_read_only()
        token = AuthToken.objects.create(self.regular_user, None)
        url = reverse('tokens:delete', kwargs={'pk': token[0].pk})
        self.assert_response(url, [self.regular_user, self.anonymous], 302)
