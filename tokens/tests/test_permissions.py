"""Tests for UI view permissions in the tokens app"""

from django.test import override_settings
from django.urls import reverse

from knox.models import AuthToken

# Projectroles dependency
from projectroles.tests.test_permissions import TestSiteAppPermissionBase


class TestTokenPermissions(TestSiteAppPermissionBase):
    """Tests for token view permissions"""

    def test_get_list(self):
        """Test tUserTokenListView GET"""
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_list_anon(self):
        """Test UserTokenListView GET with anonymous access"""
        url = reverse('tokens:list')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_create(self):
        """Test UserTokenCreateView GET"""
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_create_anon(self):
        """Test UserTokenCreateView GET with anonymous access"""
        url = reverse('tokens:create')
        self.assert_response(url, [self.superuser, self.regular_user], 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_delete(self):
        """Test UserTokenDeleteView GET"""
        token = AuthToken.objects.create(self.regular_user, None)
        url = reverse('tokens:delete', kwargs={'pk': token[0].pk})
        self.assert_response(url, self.regular_user, 200)
        self.assert_response(url, self.anonymous, 302)
