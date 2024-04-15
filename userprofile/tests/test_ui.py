"""UI tests for the userprofile app"""

from django.test import override_settings
from django.urls import reverse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.forms import SETTING_DISABLE_LABEL
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_ui import UITestBase


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']


@override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
class TestUserDetails(UITestBase):
    """Tests for user details page"""

    def setUp(self):
        super().setUp()
        # Create users
        self.local_user = self.make_user('local_user', False)
        self.ldap_user = self.make_user('user@EXAMPLE', False)

    def test_update_button(self):
        """Test existence of user update button"""
        url = reverse('userprofile:detail')
        expected = [(self.local_user, 1), (self.ldap_user, 0)]
        self.assert_element_count(expected, url, 'sodar-user-btn-update')


class TestUserSettings(UITestBase):
    """Tests for user settings page"""

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
                'div[id="div_id_settings.projectroles.'
                'user_email_additional"] label',
            )
        )
        input_elem = self.selenium.find_element(
            By.CSS_SELECTOR,
            'input[id="id_settings.projectroles.user_email_additional"]',
        )
        self.assertIsNone(input_elem.get_attribute('disabled'))
        label = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div[id="div_id_settings.projectroles.'
            'user_email_additional"] label',
        )
        self.assertNotIn(SETTING_DISABLE_LABEL, label.text)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_global_setting_target(self):
        """Test global user setting on target site"""
        self.login_and_redirect(self.superuser, self.url)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_settings.projectroles.'
                'user_email_additional"]',
            )
        )
        input_elem = self.selenium.find_element(
            By.CSS_SELECTOR,
            'input[id="id_settings.projectroles.user_email_additional"]',
        )
        self.assertIsNotNone(input_elem.get_attribute('disabled'))
        label = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div[id="div_id_settings.projectroles.'
            'user_email_additional"] label',
        )
        self.assertIn(SETTING_DISABLE_LABEL, label.text)
