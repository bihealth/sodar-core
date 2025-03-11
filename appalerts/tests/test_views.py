"""UI and Ajax view tests for the appalerts app"""

from django.urls import reverse

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI

from appalerts.tests.test_models import AppAlertMixin


app_settings = AppSettingAPI()


# Local constants
APP_NAME_PR = 'projectroles'


class ViewTestBase(AppAlertMixin, TestCase):
    """Base class for appalerts view testing"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        self.no_alert_user = self.make_user('no_alert_user')
        # No user
        self.anonymous = None
        # Create alert
        self.alert = self.make_app_alert(
            user=self.regular_user, url=reverse('home')
        )


class TestAppAlertListView(ViewTestBase):
    """Tests for AppAlertListView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('appalerts:list')

    def test_get_superuser(self):
        """Test AppAlertListView GET as superuser"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 0)
        self.assertEqual(response.context['read_only_disable'], False)

    def test_get_regular_user(self):
        """Test GET as user with assigned alert"""
        with self.login(self.regular_user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 1)
        self.assertEqual(response.context['object_list'][0].pk, self.alert.pk)
        self.assertEqual(response.context['read_only_disable'], False)

    def test_get_no_alert_user(self):
        """Test GET as user without alerts"""
        with self.login(self.no_alert_user):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object_list'].count(), 0)
        self.assertEqual(response.context['read_only_disable'], False)

    def test_get_read_only_superuser(self):
        """Test GET with site read-only mode as superuser"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['read_only_disable'], False)

    def test_get_read_only_regular_user(self):
        """Test GET with site read-only mode as regular user"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        with self.login(self.regular_user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['read_only_disable'], True)


class TestAppAlertRedirectView(ViewTestBase):
    """Tests for AppAlertLinkRedirectView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'appalerts:redirect',
            kwargs={'appalert': self.alert.sodar_uuid},
        )
        self.list_url = reverse('appalerts:list')

    def test_get_superuser(self):
        """Test AppAlertLinkRedirectView GET as superuser"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.superuser):
            response = self.client.get(self.url)
            self.assertRedirects(response, self.list_url)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)

    def test_get_regular_user(self):
        """Test GET as user with assigned alert"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.regular_user):
            response = self.client.get(self.url)
            self.assertRedirects(response, self.alert.url)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, False)

    def test_get_no_alert_user(self):
        """Test GET as user without alerts"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.no_alert_user):
            response = self.client.get(self.url)
            self.assertRedirects(response, self.list_url)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)


class TestAppAlertStatusAjaxView(ViewTestBase):
    """Tests for AppAlertStatusAjaxView"""

    def test_get_user_with_alerts(self):
        """Test AppAlertStatusAjaxView GET as user with alert assigned"""
        with self.login(self.regular_user):
            response = self.client.get(reverse('appalerts:ajax_status'))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['alerts'], 1)

    def test_get_user_no_alerts(self):
        """Test GET as user without alert assigned"""
        with self.login(self.no_alert_user):
            response = self.client.get(reverse('appalerts:ajax_status'))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['alerts'], 0)


class TestAppAlertDismissAjaxView(ViewTestBase):
    """Tests for AppAlertDismissAjaxView"""

    def test_post_superuser(self):
        """Test AppAlertDismissAjaxView POST as superuser"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.superuser):
            response = self.client.post(
                reverse(
                    'appalerts:ajax_dismiss',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)

    def test_post_regular_user(self):
        """Test POST as user with assigned alert"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.regular_user):
            response = self.client.post(
                reverse(
                    'appalerts:ajax_dismiss',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, False)

    def test_post_no_alert_user(self):
        """Test POST as user without alerts"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.no_alert_user):
            response = self.client.post(
                reverse(
                    'appalerts:ajax_dismiss',
                    kwargs={'appalert': self.alert.sodar_uuid},
                )
            )
            self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)

    def test_post_regular_user_all(self):
        """Test POST as user dismissing all alerts"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.regular_user):
            response = self.client.post(reverse('appalerts:ajax_dismiss_all'))
            self.assertEqual(response.status_code, 200)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, False)

    def test_post_no_alert_user_all(self):
        """Test POST as user without alerts trying to dismiss all"""
        self.assertEqual(self.alert.active, True)
        with self.login(self.no_alert_user):
            response = self.client.post(reverse('appalerts:ajax_dismiss_all'))
            self.assertEqual(response.status_code, 404)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.active, True)
