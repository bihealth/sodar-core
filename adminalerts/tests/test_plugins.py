"""Plugin tests for the adminalerts app"""

from test_plus.test import TestCase

from django.urls import reverse

# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from adminalerts.models import AdminAlertDismissal
from adminalerts.urls import urlpatterns
from adminalerts.tests.test_models import AdminAlertMixin


PLUGIN_NAME = 'adminalerts'
PLUGIN_TITLE = 'Admin Alerts'
PLUGIN_URL_ID = 'adminalerts:list'


# NOTE: Setting up the plugin is done during migration


class TestPlugins(AdminAlertMixin, TestCase):
    """Test adminalerts plugin"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        # Create alert
        self.alert = self.make_alert(
            message='alert',
            user=self.superuser,
            description='description',
            active=True,
        )

    def test_plugin_retrieval(self):
        """Test retrieving the plugin from the database"""
        plugin = SiteAppPluginPoint.get_plugin(PLUGIN_NAME)
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.get_model().name, PLUGIN_NAME)
        self.assertEqual(plugin.name, PLUGIN_NAME)
        self.assertEqual(plugin.get_model().title, PLUGIN_TITLE)
        self.assertEqual(plugin.title, PLUGIN_TITLE)
        self.assertEqual(plugin.entry_point_url_id, PLUGIN_URL_ID)

    def test_plugin_urls(self):
        """Test plugin URLs to ensure they're the same as in the app config"""
        plugin = SiteAppPluginPoint.get_plugin(PLUGIN_NAME)
        self.assertEqual(plugin.urls, urlpatterns)

    def test_get_messages(self):
        """Test the get_messages() function"""
        plugin = SiteAppPluginPoint.get_plugin(PLUGIN_NAME)
        messages = plugin.get_messages(self.regular_user)
        message = messages[0]
        self.assertEqual(len(messages), 1)
        self.assertIn(self.alert.message, message['content'])
        self.assertEqual(message['color'], 'info')
        self.assertEqual(message['dismissable'], True)
        self.assertEqual(message['require_auth'], True)
        self.assertEqual(
            message['dismiss_url'],
            reverse(
                'adminalerts:ajax_dismiss',
                kwargs={'adminalert': self.alert.sodar_uuid},
            ),
        )

    def test_get_messages_anonymous(self):
        """Test the get_messages() function for anonymous users"""
        plugin = SiteAppPluginPoint.get_plugin(PLUGIN_NAME)
        messages = plugin.get_messages()
        message = messages[0]
        self.assertEqual(len(messages), 1)
        self.assertIn(self.alert.message, message['content'])
        self.assertEqual(message['color'], 'info')
        self.assertEqual(message['dismissable'], False)
        self.assertEqual(message['require_auth'], True)
        self.assertEqual(
            message['dismiss_url'],
            reverse(
                'adminalerts:ajax_dismiss',
                kwargs={'adminalert': self.alert.sodar_uuid},
            ),
        )

    def test_get_dismissed_messages(self):
        """Test message dismissal"""
        plugin = SiteAppPluginPoint.get_plugin(PLUGIN_NAME)
        messages_before = plugin.get_messages(self.superuser)
        self.assertEqual(len(messages_before), 1)
        AdminAlertDismissal.objects.create(
            user=self.superuser, alert=self.alert
        )
        messages_after_superuser = plugin.get_messages(self.superuser)
        messages_after_regular_user = plugin.get_messages(self.regular_user)
        self.assertEqual(len(messages_after_superuser), 0)
        self.assertEqual(len(messages_after_regular_user), 1)
        AdminAlertDismissal.objects.create(
            user=self.regular_user, alert=self.alert
        )
        messages_after_regular_user = plugin.get_messages(self.regular_user)
        self.assertEqual(len(messages_after_regular_user), 0)
