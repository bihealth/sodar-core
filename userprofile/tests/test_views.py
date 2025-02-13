"""Tests for views in the userprofile Django app"""

import uuid

from django.contrib import auth
from django.contrib.messages import get_messages
from django.core import mail
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse

from test_plus.test import TestCase

# Timeline dependency
from timeline.models import TimelineEvent

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODARUserAdditionalEmail, SODAR_CONSTANTS
from projectroles.tests.test_models import (
    EXAMPLE_APP_NAME,
    AppSettingMixin,
    SODARUserAdditionalEmailMixin,
)
from projectroles.views import FORM_INVALID_MSG
from projectroles.utils import build_secret

from userprofile.views import (
    SETTING_UPDATE_MSG,
    EMAIL_NOT_FOUND_MSG,
    EMAIL_ALREADY_VERIFIED_MSG,
    EMAIL_VERIFIED_MSG,
    EMAIL_VERIFY_RESEND_MSG,
)


app_settings = AppSettingAPI()
User = auth.get_user_model()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
INVALID_VALUE = 'INVALID VALUE'
ADD_EMAIL = 'add1@example.com'
ADD_EMAIL2 = 'add2@example.com'
ADD_EMAIL_SECRET = build_secret(32)


class UserViewTestBase(TestCase):
    """Base class for view testing"""

    def setUp(self):
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()


# View tests -------------------------------------------------------------------


class TestUserDetailView(SODARUserAdditionalEmailMixin, UserViewTestBase):
    """Tests for UserDetailView"""

    def test_get(self):
        """Test UserDetailView GET"""
        with self.login(self.user):
            response = self.client.get(reverse('userprofile:detail'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['user_settings'])
        self.assertEqual(response.context['add_emails'].count(), 0)

    def test_get_additional_email(self):
        """Test GET with additional email"""
        self.make_email(self.user, 'add@example.com')
        self.make_email(self.user, 'add_unverified@example.com', verified=False)
        with self.login(self.user):
            response = self.client.get(reverse('userprofile:detail'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['user_settings'])
        self.assertEqual(response.context['add_emails'].count(), 2)


class TestUserAppSettingsView(AppSettingMixin, UserViewTestBase):
    """Tests for UserAppSettingsView"""

    def _get_setting(self, name):
        return app_settings.get(EXAMPLE_APP_NAME, name, user=self.user)

    def setUp(self):
        super().setUp()
        # Init test setting
        self.setting_str = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_str_setting',
            setting_type=APP_SETTING_TYPE_STRING,
            value='test',
            user=self.user,
        )
        # Init integer setting
        self.setting_int = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_int_setting',
            setting_type=APP_SETTING_TYPE_INTEGER,
            value=170,
            user=self.user,
        )
        # Init test setting with options
        self.setting_str_options = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_str_setting_options',
            setting_type=APP_SETTING_TYPE_STRING,
            value='string1',
            user=self.user,
        )
        # Init integer setting with options
        self.setting_int_options = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_int_setting_options',
            setting_type=APP_SETTING_TYPE_INTEGER,
            value=0,
            user=self.user,
        )
        # Init boolean setting
        self.setting_bool = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            user=self.user,
        )
        # Init json setting
        self.setting_json = self.make_setting(
            plugin_name=EXAMPLE_APP_NAME,
            name='user_json_setting',
            setting_type=APP_SETTING_TYPE_JSON,
            value=None,
            value_json={'Test': 'More'},
            user=self.user,
        )

    def test_get(self):
        """Test UserAppSettingsView GET"""
        with self.login(self.user):
            response = self.client.get(reverse('userprofile:settings_update'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])
        field = response.context['form'].fields.get(
            'settings.example_project_app.user_str_setting'
        )
        self.assertIsNotNone(field)
        self.assertEqual(field.widget.attrs['placeholder'], 'Example string')
        field = response.context['form'].fields.get(
            'settings.example_project_app.user_int_setting'
        )
        self.assertIsNotNone(field)
        self.assertEqual(field.widget.attrs['placeholder'], 0)
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.example_project_app.user_str_setting_options'
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.example_project_app.user_int_setting_options'
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.example_project_app.user_bool_setting'
            )
        )
        self.assertIsNotNone(
            response.context['form'].fields.get(
                'settings.example_project_app.user_json_setting'
            )
        )

    def test_post(self):
        """Test POST"""
        self.assertEqual(self._get_setting('user_str_setting'), 'test')
        self.assertEqual(self._get_setting('user_int_setting'), 170)
        self.assertEqual(
            self._get_setting('user_str_setting_options'), 'string1'
        )
        self.assertEqual(self._get_setting('user_int_setting_options'), 0)
        self.assertEqual(self._get_setting('user_bool_setting'), True)
        self.assertEqual(
            self._get_setting('user_json_setting'), {'Test': 'More'}
        )

        values = {
            'settings.example_project_app.user_str_setting': 'another-text',
            'settings.example_project_app.user_int_setting': '123',
            'settings.example_project_app.user_str_setting_options': 'string2',
            'settings.example_project_app.user_int_setting_options': 1,
            'settings.example_project_app.user_bool_setting': False,
            'settings.example_project_app.'
            'user_json_setting': '{"Test": "Less"}',
            'settings.example_project_app.user_callable_setting': 'Test',
            'settings.example_project_app.user_callable_setting_options': str(
                self.user.sodar_uuid
            ),
            'settings.projectroles.project_list_highlight': False,
            'settings.projectroles.project_list_pagination': 10,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse('userprofile:settings_update'), values
            )

        # Assert redirect
        with self.login(self.user):
            self.assertRedirects(response, reverse('userprofile:detail'))
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            SETTING_UPDATE_MSG,
        )
        # Assert settings state after update
        self.assertEqual(self._get_setting('user_str_setting'), 'another-text')
        self.assertEqual(self._get_setting('user_int_setting'), 123)
        self.assertEqual(
            self._get_setting('user_str_setting_options'), 'string2'
        )
        self.assertEqual(self._get_setting('user_int_setting_options'), 1)
        self.assertEqual(self._get_setting('user_bool_setting'), False)
        self.assertEqual(
            self._get_setting('user_json_setting'), {'Test': 'Less'}
        )
        self.assertEqual(self._get_setting('user_callable_setting'), 'Test')
        self.assertEqual(
            self._get_setting('user_callable_setting_options'),
            str(self.user.sodar_uuid),
        )

    def test_post_custom_validation(self):
        """Test POST with custom validation and invalid value"""
        values = {
            'settings.example_project_app.' 'user_str_setting': INVALID_VALUE,
            'settings.example_project_app.user_int_setting': '170',
            'settings.example_project_app.user_str_setting_options': 'string1',
            'settings.example_project_app.user_int_setting_options': '0',
            'settings.example_project_app.user_bool_setting': True,
            'settings.example_project_app.'
            'user_json_setting': '{"Test": "More"}',
            'settings.example_project_app.user_callable_setting': 'Test',
            'settings.example_project_app.user_callable_setting_options': str(
                self.user.sodar_uuid
            ),
            'settings.projectroles.project_list_highlight': False,
            'settings.projectroles.project_list_pagination': 10,
        }
        with self.login(self.user):
            response = self.client.post(
                reverse('userprofile:settings_update'), values
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            FORM_INVALID_MSG,
        )
        self.assertEqual(self._get_setting('user_str_setting'), 'test')


class TestUserEmailCreateView(SODARUserAdditionalEmailMixin, UserViewTestBase):
    """Tests for UserEmailCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('userprofile:email_create')
        self.url_redirect = reverse('userprofile:detail')

    def test_get(self):
        """Test UserEmailCreateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['form'])

    @override_settings(PROJECTROLES_SEND_EMAIL=False)
    def test_get_email_disabled(self):
        """Test GET with disabled email sending"""
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertRedirects(response, self.url_redirect)

    def test_post(self):
        """Test POST"""
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='email_create').count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            data = {
                'user': self.user.pk,
                'email': ADD_EMAIL,
                'secret': ADD_EMAIL_SECRET,
            }
            response = self.client.post(self.url, data)
            self.assertRedirects(response, self.url_redirect)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        email = SODARUserAdditionalEmail.objects.first()
        expected = {
            'id': email.pk,
            'user': self.user.pk,
            'email': ADD_EMAIL,
            'secret': ADD_EMAIL_SECRET,
            'verified': False,
            'sodar_uuid': email.sodar_uuid,
        }
        self.assertEqual(model_to_dict(email), expected)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='email_create').count(), 1
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].recipients(), [ADD_EMAIL])
        verify_url = reverse(
            'userprofile:email_verify', kwargs={'secret': email.secret}
        )
        self.assertIn(verify_url, mail.outbox[0].body)

    def test_post_existing_primary(self):
        """Test POST with email used as primary email for user"""
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='email_create').count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            data = {
                'user': self.user.pk,
                'email': self.user.email,
                'secret': ADD_EMAIL_SECRET,
            }
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='email_create').count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_existing_additional(self):
        """Test POST with email used as additional email for user"""
        self.make_email(self.user, ADD_EMAIL)
        with self.login(self.user):
            data = {
                'user': self.user.pk,
                'email': ADD_EMAIL,
                'secret': ADD_EMAIL_SECRET,
            }
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

    def test_post_multiple(self):
        """Test POST with different existing additional email"""
        self.make_email(self.user, ADD_EMAIL)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            data = {
                'user': self.user.pk,
                'email': ADD_EMAIL2,
                'secret': ADD_EMAIL_SECRET,
            }
            response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 1)


class TestUserEmailVerifyView(SODARUserAdditionalEmailMixin, UserViewTestBase):
    """Tests for UserEmailVerifyView"""

    def setUp(self):
        super().setUp()
        self.url_redirect = reverse('userprofile:detail')
        self.email = self.make_email(self.user, ADD_EMAIL, verified=False)
        self.url = reverse(
            'userprofile:email_verify', kwargs={'secret': self.email.secret}
        )

    def test_get(self):
        """Test UserEmailVerifyView GET"""
        self.assertEqual(self.email.verified, False)
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertRedirects(response, self.url_redirect)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, True)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_VERIFIED_MSG.format(email=self.email.email),
        )

    def test_get_invalid_secret(self):
        """Test GET with invalid secret"""
        self.assertEqual(self.email.verified, False)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'userprofile:email_verify',
                    kwargs={'secret': build_secret(32)},
                )
            )
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, False)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_NOT_FOUND_MSG,
        )

    def test_get_wrong_user(self):
        """Test GET with wrong user"""
        user_new = self.make_user('user_new')
        self.assertEqual(self.email.verified, False)
        with self.login(user_new):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, False)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_NOT_FOUND_MSG,
        )

    def test_get_verified(self):
        """Test GET with verified email"""
        self.email.verified = True
        self.email.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, True)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_ALREADY_VERIFIED_MSG,
        )


class TestUserEmailVerifyResendView(
    SODARUserAdditionalEmailMixin, UserViewTestBase
):
    """Tests for UserEmailVerifyResendView"""

    def setUp(self):
        super().setUp()
        self.url_redirect = reverse('userprofile:detail')
        self.email = self.make_email(self.user, ADD_EMAIL, verified=False)
        self.url = reverse(
            'userprofile:email_verify_resend',
            kwargs={'sodaruseradditionalemail': self.email.sodar_uuid},
        )

    def test_get(self):
        """Test UserEmailVerifyResendView GET"""
        self.assertEqual(len(mail.outbox), 0)
        with self.login(self.user):
            response = self.client.get(self.url)
            self.assertRedirects(response, self.url_redirect)
        self.email.refresh_from_db()
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_VERIFY_RESEND_MSG.format(email=self.email.email),
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        self.assertEqual(self.email.verified, False)
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'userprofile:email_verify_resend',
                    kwargs={'sodaruseradditionalemail': uuid.uuid4()},
                )
            )
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, False)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_NOT_FOUND_MSG,
        )

    def test_get_wrong_user(self):
        """Test GET with wrong user"""
        user_new = self.make_user('user_new')
        self.assertEqual(self.email.verified, False)
        with self.login(user_new):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, False)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_NOT_FOUND_MSG,
        )

    def test_get_verified(self):
        """Test GET with verified email"""
        self.email.verified = True
        self.email.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.email.refresh_from_db()
        self.assertEqual(self.email.verified, True)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            EMAIL_ALREADY_VERIFIED_MSG,
        )


class TestUserEmailDeleteView(SODARUserAdditionalEmailMixin, UserViewTestBase):
    """Tests for UserEmailDeleteView"""

    def setUp(self):
        super().setUp()
        self.url_redirect = reverse('userprofile:detail')
        self.email = self.make_email(self.user, ADD_EMAIL, verified=False)
        self.url = reverse(
            'userprofile:email_delete',
            kwargs={'sodaruseradditionalemail': self.email.sodar_uuid},
        )

    def test_get(self):
        """Test UserEmailDeleteView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.email)

    def test_post(self):
        """Test POST"""
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url)
            self.assertRedirects(response, self.url_redirect)
        self.assertEqual(SODARUserAdditionalEmail.objects.count(), 0)
