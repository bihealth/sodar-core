"""Tests for UI view permissions in the siteinfo app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions import SiteAppPermissionTestBase


class TestSiteInfoViewPermissions(SiteAppPermissionTestBase):
    """Tests for SiteInfoView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('siteinfo:info')

    def test_site_info(self):
        """Test SiteInfoView GET"""
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_site_info_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 302)
