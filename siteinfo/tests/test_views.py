"""Tests for views in the siteinfo app"""

from django.test import override_settings
from django.urls import reverse

from test_plus.test import TestCase

from adminalerts.plugins import SiteAppPlugin as AdminAlertsSitePlugin
from projectroles.tests.base import SiteAppPermissionTestBase


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


class TestPluginStatisticsAjaxView(SiteAppPermissionTestBase):
    """Tests for PluginStatisticsAjaxView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('siteinfo:ajax_stats')

    def test_get(self):
        """Test TestPluginStatisticsAjaxView GET"""
        with self.login(self.superuser):
            res = self.get(self.url).json()
        # Test existing plugins (only plugins with stats will be returned)
        self.assertListEqual(
            list(res.keys()),
            [
                'adminalerts',
                'example_backend_app',
                'example_project_app',
                'filesfolders',
                'timeline',
            ],
        )
        # Test presence of all required fields
        for v in res.values():
            self.assertIsNotNone(v.get('title'))
            self.assertIsNotNone(v.get('icon'))
            self.assertIsNotNone(v.get('stats'))
        # Test stat values
        self.assertDictEqual(
            res['adminalerts']['stats']['alert_count'],
            {
                'label': 'Alerts',
                'value': 0,
                'info_cls': 'col-md-7',
                'info_val': 0,
            },
        )
        self.assertDictEqual(
            res['example_backend_app']['stats']['backend_example_stat'],
            {
                'label': 'Backend example',
                'value': True,
                'info_cls': 'col-md-7',
                'info_val': True,
            },
        )

    def test_get_stats_error(self):
        """Test GET with error from get_statistics()"""

        def get_statistics_error(self):
            raise ValueError('Invalid Stats')

        # Monkey-patch the get_statistics() function to trigger an error
        get_statistics_original = AdminAlertsSitePlugin.get_statistics
        AdminAlertsSitePlugin.get_statistics = get_statistics_error

        with self.login(self.superuser):
            res = self.get(self.url).json()
        self.assertEqual(res['adminalerts']['error'], 'Invalid Stats')
        # Test that other plugins still work
        self.assertDictEqual(
            res['example_backend_app']['stats']['backend_example_stat'],
            {
                'label': 'Backend example',
                'value': True,
                'info_cls': 'col-md-7',
                'info_val': True,
            },
        )

        AdminAlertsSitePlugin.get_statistics = get_statistics_original

    @override_settings(ENABLED_BACKEND_PLUGINS=[])
    def test_get_stats_inactive(self):
        """Test GET with inactive backend plugins"""
        with self.login(self.superuser):
            res = self.get(self.url).json()
        self.assertNotIn('example_backend_app', res.keys())
