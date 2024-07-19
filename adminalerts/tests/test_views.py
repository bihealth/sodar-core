"""Tests for UI views in the adminalerts app"""

from django.conf import settings
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.tests.test_models import SODARUserAdditionalEmailMixin

from adminalerts.models import AdminAlert
from adminalerts.tests.test_models import AdminAlertMixin
from adminalerts.views import EMAIL_SUBJECT


app_settings = AppSettingAPI()


# Local constants
APP_NAME = 'adminalerts'
ALERT_MSG = 'New alert'
ALERT_MSG_UPDATED = 'Updated alert'
ALERT_DESC = 'Description'
ALERT_DESC_UPDATED = 'Updated description'
ALERT_DESC_MARKDOWN = '## Description'
EMAIL_DESC_LEGEND = 'Additional details'
ADD_EMAIL = 'add1@example.com'
ADD_EMAIL2 = 'add2@example.com'


class AdminalertsViewTestBase(
    AdminAlertMixin, SODARUserAdditionalEmailMixin, TestCase
):
    """Base class for adminalerts view testing"""

    def _make_alert(self):
        return self.make_alert(
            message=ALERT_MSG,
            user=self.superuser,
            description=ALERT_DESC,
            active=True,
            require_auth=True,
        )

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.user_regular = self.make_user('user_regular')
        # No user
        self.anonymous = None
        self.expiry_str = (
            timezone.now() + timezone.timedelta(days=1)
        ).strftime('%Y-%m-%d')


class TestAdminAlertListView(AdminalertsViewTestBase):
    """Tests for AdminAlertListView"""

    def setUp(self):
        super().setUp()
        self.alert = self._make_alert()

    def test_get(self):
        """Test AdminAlertListView GET"""
        with self.login(self.superuser):
            response = self.client.get(reverse('adminalerts:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['object_list'])
        self.assertEqual(response.context['object_list'][0].pk, self.alert.pk)


class TestAdminAlertDetailView(AdminalertsViewTestBase):
    """Tests for AdminAlertDetailView"""

    def setUp(self):
        super().setUp()
        self.alert = self._make_alert()

    def test_get(self):
        """Test AdminAlertDetailView GET"""
        with self.login(self.superuser):
            response = self.client.get(
                reverse(
                    'adminalerts:detail',
                    kwargs={'adminalert': self.alert.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.alert)


class TestAdminAlertCreateView(AdminalertsViewTestBase):
    """Tests for AdminAlertCreateView"""

    def _get_post_data(self, **kwargs):
        ret = {
            'message': ALERT_MSG,
            'description': ALERT_DESC,
            'date_expire': self.expiry_str,
            'active': True,
            'require_auth': True,
            'send_email': True,
        }
        ret.update(**kwargs)
        return ret

    def setUp(self):
        super().setUp()
        self.url = reverse('adminalerts:create')

    def test_get(self):
        """Test AdminAlertCreateView GET"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test POST"""
        self.assertEqual(AdminAlert.objects.all().count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            EMAIL_SUBJECT.format(state='New', message=ALERT_MSG),
            mail.outbox[0].subject,
        )
        self.assertEqual(
            mail.outbox[0].recipients(),
            [settings.EMAIL_SENDER, self.user_regular.email],
        )
        self.assertEqual(mail.outbox[0].to, [settings.EMAIL_SENDER])
        self.assertEqual(mail.outbox[0].bcc, [self.user_regular.email])
        self.assertIn(ALERT_MSG, mail.outbox[0].body)
        self.assertIn(EMAIL_DESC_LEGEND, mail.outbox[0].body)
        self.assertIn(ALERT_DESC, mail.outbox[0].body)

    def test_post_no_description(self):
        """Test POST with no description"""
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(description='')
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(ALERT_MSG, mail.outbox[0].body)
        self.assertNotIn(EMAIL_DESC_LEGEND, mail.outbox[0].body)

    def test_post_markdown_description(self):
        """Test POST with markdown description"""
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(description=ALERT_DESC_MARKDOWN)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(ALERT_MSG, mail.outbox[0].body)
        self.assertIn(EMAIL_DESC_LEGEND, mail.outbox[0].body)
        # Description should be provided in raw format
        self.assertIn(ALERT_DESC_MARKDOWN, mail.outbox[0].body)

    def test_post_no_email(self):
        """Test POST with no email to be sent"""
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(send_email=False)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_inactive(self):
        """Test POST with inactive state"""
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(active=False)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_multiple_users(self):
        """Test POST with multiple users"""
        user_new = self.make_user('user_new')
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].recipients(),
            [settings.EMAIL_SENDER, user_new.email, self.user_regular.email],
        )
        self.assertIn(ALERT_MSG, mail.outbox[0].body)
        self.assertIn(EMAIL_DESC_LEGEND, mail.outbox[0].body)
        self.assertIn(ALERT_DESC, mail.outbox[0].body)

    def test_post_add_email_regular_user(self):
        """Test POST with additional emails on regular user"""
        self.make_email(self.user_regular, ADD_EMAIL)
        self.make_email(self.user_regular, ADD_EMAIL2)
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].recipients(),
            [
                settings.EMAIL_SENDER,
                self.user_regular.email,
                ADD_EMAIL,
                ADD_EMAIL2,
            ],
        )

    def test_post_add_email_regular_user_unverified(self):
        """Test POST with additional and unverified emails on regular user"""
        self.make_email(self.user_regular, ADD_EMAIL)
        self.make_email(self.user_regular, ADD_EMAIL2, verified=False)
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].recipients(),
            [
                settings.EMAIL_SENDER,
                self.user_regular.email,
                ADD_EMAIL,
            ],
        )

    def test_post_add_email_superuser(self):
        """Test POST with additional emails on superuser"""
        self.make_email(self.superuser, ADD_EMAIL)
        self.make_email(self.superuser, ADD_EMAIL2)
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        # Superuser additional emails should not be included
        self.assertEqual(
            mail.outbox[0].recipients(),
            [settings.EMAIL_SENDER, self.user_regular.email],
        )

    def test_post_email_disable(self):
        """Test POST with email notifications disabled"""
        app_settings.set(
            APP_NAME, 'notify_email_alert', False, user=self.user_regular
        )
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_expired(self):
        """Test POST with old expiry date (should fail)"""
        self.assertEqual(AdminAlert.objects.all().count(), 0)
        expire_fail = (timezone.now() + timezone.timedelta(days=-1)).strftime(
            '%Y-%m-%d'
        )
        data = self._get_post_data(date_expire=expire_fail)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AdminAlert.objects.all().count(), 0)


class TestAdminAlertUpdateView(AdminalertsViewTestBase):
    """Tests for AdminAlertUpdateView"""

    def _get_post_data(self, **kwargs):
        ret = {
            'message': ALERT_MSG_UPDATED,
            'description': ALERT_DESC_UPDATED,
            'date_expire': self.expiry_str,
            'active': False,
            'require_auth': True,
            'send_email': False,
        }
        ret.update(kwargs)
        return ret

    def setUp(self):
        super().setUp()
        self.alert = self._make_alert()
        self.url = reverse(
            'adminalerts:update',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_get(self):
        """Test AdminAlertUpdateView GET"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test POST"""
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data()
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.message, ALERT_MSG_UPDATED)
        self.assertEqual(self.alert.description.raw, ALERT_DESC_UPDATED)
        self.assertEqual(self.alert.active, False)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_email(self):
        """Test POST with email update enabled"""
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(active=True, send_email=True)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            EMAIL_SUBJECT.format(state='Updated', message=ALERT_MSG_UPDATED),
            mail.outbox[0].subject,
        )
        self.assertEqual(
            mail.outbox[0].recipients(),
            [settings.EMAIL_SENDER, self.user_regular.email],
        )

    def test_post_email_inactive(self):
        """Test POST with email update enabled and inactive alert"""
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(send_email=True)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)  # No email for inactive event

    def test_post_email_disable(self):
        """Test POST with disabled email notifications"""
        app_settings.set(
            APP_NAME, 'notify_email_alert', False, user=self.user_regular
        )
        self.assertEqual(len(mail.outbox), 0)
        data = self._get_post_data(active=True, send_email=True)
        with self.login(self.superuser):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_user(self):
        """Test POST by different user"""
        superuser2 = self.make_user('superuser2')
        superuser2.is_superuser = True
        superuser2.save()
        data = self._get_post_data()
        with self.login(superuser2):
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.user, superuser2)


class TestAdminAlertDeleteView(AdminalertsViewTestBase):
    """Tests for AdminAlertDeleteView"""

    def setUp(self):
        super().setUp()
        self.alert = self._make_alert()
        self.url = reverse(
            'adminalerts:delete',
            kwargs={'adminalert': self.alert.sodar_uuid},
        )

    def test_get(self):
        """Test AdminAlertDeleteView GET"""
        with self.login(self.superuser):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test POST"""
        self.assertEqual(AdminAlert.objects.all().count(), 1)
        with self.login(self.superuser):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('adminalerts:list'))
        self.assertEqual(AdminAlert.objects.all().count(), 0)
