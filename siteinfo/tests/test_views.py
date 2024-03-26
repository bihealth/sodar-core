"""Tests for views in the siteinfo app"""

from django.urls import reverse

from test_plus.test import TestCase


class TestSiteInfoView(TestCase):
    """Tests for SiteInfoView"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        # No user
        self.anonymous = None

    def test_get(self):
        """Test SiteInfoView GET"""
        with self.login(self.superuser):
            response = self.client.get(reverse('siteinfo:info'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['project_plugins'])
        self.assertIsNotNone(response.context['site_plugins'])
        self.assertIsNotNone(response.context['backend_plugins'])
        self.assertIsNotNone(response.context['settings_core'])
