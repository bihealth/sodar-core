"""Tests for UI view permissions in the tokens app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.base import SiteAppPermissionTestBase

from tokens.models import SODARAuthToken
from tokens.tests.test_models import SODARAuthTokenMixin


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']


class TestTokensPermissions(SODARAuthTokenMixin, SiteAppPermissionTestBase):
    """Tests for token view permissions"""

    def test_get_list(self):
        """Test TokenListView GET"""
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_list_anon(self):
        """Test TokenListView GET with anonymous access"""
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_list_read_only(self):
        """Test TokenListView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_create(self):
        """Test TokenCreateView GET"""
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_get_create_restrict(self):
        """Test TokenCreateView GET with restricted creation"""
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
        """Test TokenCreateView GET with anonymous access"""
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_create_read_only(self):
        """Test TokenCreateView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('tokens:create')
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, [self.regular_user, self.anonymous], 302)

    def test_get_delete(self):
        """Test TokenDeleteView GET"""
        token = SODARAuthToken.objects.create(self.regular_user, None)
        url = reverse('tokens:delete', kwargs={'pk': token[0].pk})
        self.assert_response(url, self.regular_user, 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_delete_read_only(self):
        """Test TokenDeleteView GET with site read-only mode"""
        self.set_site_read_only()
        token = SODARAuthToken.objects.create(self.regular_user, None)
        url = reverse('tokens:delete', kwargs={'pk': token[0].pk})
        self.assert_response(url, [self.regular_user, self.anonymous], 302)
