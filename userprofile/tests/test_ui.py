"""UI tests for the userprofile app"""

from django.test import override_settings
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.tests.test_ui import TestUIBase


@override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
class TestUserDetails(TestUIBase):
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


class TestUserSettings(TestUIBase):
    """Tests for user settings page"""

    def setUp(self):
        super().setUp()
        # Create users
        self.local_user = self.make_user('local_user', False)
        self.ldap_user = self.make_user('user@EXAMPLE', False)

    def test_settings_label_icon(self):
        """Test existence of settings label icon"""
        url = reverse('userprofile:settings_update')
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
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
