"""Tests for views in the userprofile Django app"""

from django.contrib import auth
from django.contrib.messages import get_messages
from django.urls import reverse

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.tests.test_models import EXAMPLE_APP_NAME, AppSettingMixin
from projectroles.views import MSG_FORM_INVALID

from userprofile.views import SETTING_UPDATE_MSG


app_settings = AppSettingAPI()
User = auth.get_user_model()


INVALID_SETTING_VALUE = 'INVALID VALUE'


class UserViewsTestBase(TestCase):
    """Base class for view testing"""

    def setUp(self):
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()


# View tests -------------------------------------------------------------------


class TestUserDetailView(UserViewsTestBase):
    """Tests for UserDetailView"""

    def test_get(self):
        """Test UserDetailView GET"""
        with self.login(self.user):
            response = self.client.get(reverse('userprofile:detail'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['user_settings'])


class TestUserSettingsView(AppSettingMixin, UserViewsTestBase):
    """Tests for UserSettingsView"""

    def _get_setting(self, name):
        return app_settings.get(EXAMPLE_APP_NAME, name, user=self.user)

    def setUp(self):
        super().setUp()
        # Init test setting
        self.setting_str = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_str_setting',
            setting_type='STRING',
            value='test',
            user=self.user,
        )
        # Init integer setting
        self.setting_int = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_int_setting',
            setting_type='INTEGER',
            value=170,
            user=self.user,
        )
        # Init test setting with options
        self.setting_str_options = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_str_setting_options',
            setting_type='STRING',
            value='string1',
            user=self.user,
        )
        # Init integer setting with options
        self.setting_int_options = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_int_setting_options',
            setting_type='INTEGER',
            value=0,
            user=self.user,
        )
        # Init boolean setting
        self.setting_bool = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_bool_setting',
            setting_type='BOOLEAN',
            value=True,
            user=self.user,
        )
        # Init json setting
        self.setting_json = self.make_setting(
            app_name=EXAMPLE_APP_NAME,
            name='user_json_setting',
            setting_type='JSON',
            value=None,
            value_json={'Test': 'More'},
            user=self.user,
        )

    def test_get(self):
        """Test UserSettingsView GET"""
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
        """Test UserSettingsView POST"""
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
            'settings.example_project_app.'
            'user_str_setting': INVALID_SETTING_VALUE,
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
        }
        with self.login(self.user):
            response = self.client.post(
                reverse('userprofile:settings_update'), values
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(get_messages(response.wsgi_request))[0].message,
            MSG_FORM_INVALID,
        )
        self.assertEqual(self._get_setting('user_str_setting'), 'test')
