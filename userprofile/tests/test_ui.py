"""UI tests for the userprofile app"""

from django.test import override_settings
from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import APP_SETTING_DISABLE_LABEL
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import SODARUserAdditionalEmailMixin
from projectroles.tests.test_ui import UITestBase


app_settings = AppSettingAPI()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']

# Local constants
APP_NAME_PR = 'projectroles'


@override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
class TestUserDetailView(SODARUserAdditionalEmailMixin, UITestBase):
    """Tests for UserDetailView"""

    def setUp(self):
        super().setUp()
        # Create users
        self.local_user = self.make_user('local_user', False)
        self.ldap_user = self.make_user('user@EXAMPLE', False)
        self.url = reverse('userprofile:detail')

    def test_update_button(self):
        """Test existence of user update button"""
        expected = [(self.local_user, 1), (self.ldap_user, 0)]
        self.assert_element_count(expected, self.url, 'sodar-user-btn-update')

    def test_update_button_read_only(self):
        """Test existence of user update button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [(self.local_user, 0), (self.ldap_user, 0)]
        self.assert_element_count(expected, self.url, 'sodar-user-btn-update')

    def test_settings_button(self):
        """Test existence of settings update button"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 1),
        ]
        self.assert_element_count(expected, self.url, 'sodar-user-btn-settings')

    def test_settings_button_read_only(self):
        """Test existence of settings update button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, 'sodar-user-btn-settings')

    def test_add_email_button(self):
        """Test existence of add email button"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 1),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-user-btn-email-add'
        )

    def test_add_email_button_read_only(self):
        """Test existence of add email button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-user-btn-email-add'
        )

    def test_additional_email_unset(self):
        """Test existence of additional email elements without email"""
        self.assert_element_count(
            [(self.local_user, 0)],
            self.url,
            'sodar-user-email-table-row',
            'class',
        )
        self.assert_element_count(
            [(self.local_user, 0)],
            self.url,
            'sodar-user-email-dropdown',
            'class',
        )
        self.assert_element_exists(
            [self.local_user],
            self.url,
            'sodar-user-email-table-not-found',
            True,
        )

    def test_additional_email_set(self):
        """Test existence of additional email elements with email"""
        self.make_email(self.local_user, 'add1@example.com')
        self.make_email(self.local_user, 'add2@example.com', verified=False)
        # Another user, should not be visible
        self.make_email(self.ldap_user, 'add3@example.com')
        self.assert_element_count(
            [(self.local_user, 2)],
            self.url,
            'sodar-user-email-table-row',
            'class',
        )
        self.assert_element_count(
            [(self.local_user, 2)],
            self.url,
            'sodar-user-email-dropdown',
            'class',
        )
        self.assert_element_exists(
            [self.local_user],
            self.url,
            'sodar-user-email-table-not-found',
            False,
        )

    def test_additional_email_set_read_only(self):
        """Test additional email with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.make_email(self.local_user, 'add1@example.com')
        self.make_email(self.local_user, 'add2@example.com', verified=False)
        self.assert_element_count(
            [(self.local_user, 2)],
            self.url,
            'sodar-user-email-table-row',
            'class',
        )
        self.assert_element_count(
            [(self.local_user, 0)],
            self.url,
            'sodar-user-email-dropdown',
            'class',
        )

    def test_additional_email_set_read_only_superuser(self):
        """Test additional email with site read-only mode as superuser"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.make_email(self.superuser, 'add1@example.com')
        self.make_email(self.superuser, 'add2@example.com', verified=False)
        self.assert_element_count(
            [(self.superuser, 2)],
            self.url,
            'sodar-user-email-table-row',
            'class',
        )
        self.assert_element_count(
            [(self.superuser, 2)],
            self.url,
            'sodar-user-email-dropdown',
            'class',
        )

    @override_settings(PROJECTROLES_SEND_EMAIL=False)
    def test_additional_email_disabled(self):
        """Test existence of email card with PROJECTROLES_SEND_EMAIL=False"""
        self.assert_element_exists(
            [self.local_user],
            self.url,
            'sodar-user-email-card',
            False,
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_additional_email_target(self):
        """Test existence of additional email elements as target site"""
        self.make_email(self.local_user, 'add1@example.com')
        self.make_email(self.local_user, 'add2@example.com', verified=False)
        self.assert_element_exists(
            [self.local_user],
            self.url,
            'sodar-user-btn-email-add',
            False,
        )
        self.assert_element_count(
            [(self.local_user, 2)],
            self.url,
            'sodar-user-email-table-row',
            'class',
        )
        self.assert_element_count(
            [(self.local_user, 0)],
            self.url,
            'sodar-user-email-dropdown',
            'class',
        )
        self.assert_element_exists(
            [self.local_user],
            self.url,
            'sodar-user-email-table-not-found',
            False,
        )


class TestUserAppSettingsView(UITestBase):
    """Tests for UserAppSettingsView"""

    def setUp(self):
        super().setUp()
        # Create users
        self.local_user = self.make_user('local_user', False)
        self.ldap_user = self.make_user('user@EXAMPLE', False)
        self.url = reverse('userprofile:settings_update')

    def test_settings_label_icon(self):
        """Test existence of settings label icon"""
        self.login_and_redirect(self.superuser, self.url)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_settings.example_project_app.'
                'user_int_setting"] label',
            )
        )
        label = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div[id="div_id_settings.example_project_app.'
            'user_int_setting"] label',
        )
        # Wait before icon is rendered
        WebDriverWait(label, 15).until(
            lambda x: x.find_element(By.TAG_NAME, 'svg')
        )
        icon = label.find_element(By.TAG_NAME, 'svg')
        self.assertTrue(icon.is_displayed())

    def test_global_setting_source(self):
        """Test global user setting on source site"""
        self.login_and_redirect(self.superuser, self.url)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_settings.projectroles.notify_email_project"]',
            )
        )
        input_elem = self.selenium.find_element(
            By.CSS_SELECTOR,
            'input[id="id_settings.projectroles.notify_email_project"]',
        )
        self.assertIsNone(input_elem.get_attribute('disabled'))
        label = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div[id="div_id_settings.projectroles.notify_email_project"] label',
        )
        self.assertNotIn(APP_SETTING_DISABLE_LABEL, label.text)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_global_setting_target(self):
        """Test global user setting on target site"""
        self.login_and_redirect(self.superuser, self.url)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_settings.projectroles.notify_email_project"]',
            )
        )
        input_elem = self.selenium.find_element(
            By.CSS_SELECTOR,
            'input[id="id_settings.projectroles.notify_email_project"]',
        )
        self.assertIsNotNone(input_elem.get_attribute('disabled'))
        label = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div[id="div_id_settings.projectroles.notify_email_project"] label',
        )
        self.assertIn(APP_SETTING_DISABLE_LABEL, label.text)
