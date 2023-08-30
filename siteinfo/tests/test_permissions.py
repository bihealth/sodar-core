"""Permission tests for the siteinfo app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import TestSiteAppPermissionBase


class TestSiteInfoPermissions(TestSiteAppPermissionBase):
    """Tests for siteinfo view permissions"""

    def test_site_info(self):
        """Test site info view"""
        url = reverse('siteinfo:info')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_site_info_anon(self):
        """Test site info view with anonymous access"""
        url = reverse('siteinfo:info')
        self.assert_response(url, self.anonymous, 302)
