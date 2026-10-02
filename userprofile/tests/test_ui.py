"""UI tests for the userprofile app"""

from urllib.parse import urlsplit

from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import localtime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import APP_SETTING_DISABLE_LABEL
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import SODARUserAdditionalEmailMixin
from projectroles.tests.base import SiteUITestBase


app_settings = AppSettingAPI()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']

# Local constants
APP_NAME_PR = 'projectroles'
UPDATE_BTN_ID = 'sodar-user-btn-update'
SETTING_BTN_ID = 'sodar-user-btn-settings'
EMAIL_ADD_BTN_ID = 'sodar-user-btn-email-add'


@override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
class TestUserDetailView(SODARUserAdditionalEmailMixin, SiteUITestBase):
    """Tests for UserDetailView"""

    def setUp(self):
        super().setUp()
        # Create users
        self.local_user = self.make_user('local_user', False)
        self.ldap_user = self.make_user('user@EXAMPLE', False)
        self.url = reverse('userprofile:detail')
        self.url_public = reverse(
            'userprofile:detail_public',
            kwargs={'user': self.local_user.sodar_uuid},
        )

    def test_update_button(self):
        """Test existence of user update button"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, UPDATE_BTN_ID)

    def test_update_button_read_only(self):
        """Test user update button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, UPDATE_BTN_ID)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_update_button_site_mode_target(self):
        """Test user update button with target site mode"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, UPDATE_BTN_ID)

    @override_settings(PROJECTROLES_LOCAL_USER_UPDATE=False)
    def test_update_button_update_disabled_site(self):
        """Test update button with site-wide local user update disabled"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, UPDATE_BTN_ID)

    def test_update_button_update_disabled_user(self):
        """Test update button with user level local user update disabled"""
        self.local_user.enable_update = False
        self.local_user.save()
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, UPDATE_BTN_ID)

    def test_update_button_public(self):
        """Test update button in other user's public profile"""
        expected = [
            (self.superuser, 0),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url_public, UPDATE_BTN_ID)

    def test_settings_button(self):
        """Test existence of settings update button"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 1),
        ]
        self.assert_element_count(expected, self.url, SETTING_BTN_ID)

    def test_settings_button_read_only(self):
        """Test settings update button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, SETTING_BTN_ID)

    def test_settings_button_public(self):
        """Test settings update button in other user's public profile"""
        expected = [
            (self.superuser, 0),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url_public, SETTING_BTN_ID)

    def test_add_email_button(self):
        """Test existence of add email button"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 1),
        ]
        self.assert_element_count(expected, self.url, EMAIL_ADD_BTN_ID)

    def test_add_email_button_read_only(self):
        """Test add email button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [
            (self.superuser, 1),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url, EMAIL_ADD_BTN_ID)

    def test_add_email_button_public(self):
        """Test add email button in other user's public profile"""
        expected = [
            (self.superuser, 0),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(expected, self.url_public, EMAIL_ADD_BTN_ID)

    def test_additional_email_unset(self):
        """Test additional email elements without email"""
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
        """Test additional email elements with email"""
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
        """Test email card with PROJECTROLES_SEND_EMAIL=False"""
        self.assert_element_exists(
            [self.local_user],
            self.url,
            'sodar-user-email-card',
            False,
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_additional_email_target(self):
        """Test additional email elements as target site"""
        self.make_email(self.local_user, 'add1@example.com')
        self.make_email(self.local_user, 'add2@example.com', verified=False)
        self.assert_element_exists(
            [self.local_user],
            self.url,
            EMAIL_ADD_BTN_ID,
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

    def test_additional_email_public(self):
        """Test additional email elements in other user's public profile"""
        expected = [
            (self.superuser, 1),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(
            expected, self.url_public, 'sodar-user-email-card'
        )

    @override_settings(PROJECTROLES_SEND_EMAIL=False)
    def test_additional_email_public_disabled(self):
        """Test additional email in public profile with send_email disabled"""
        expected = [
            (self.superuser, 0),
            (self.local_user, 0),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(
            expected, self.url_public, 'sodar-user-email-card'
        )

    def test_add_email_dropdown_public(self):
        """Test add email dropdown in other user's public profile"""
        self.make_email(self.local_user, 'add2@example.com', verified=False)
        expected = [
            (self.superuser, 0),
            (self.local_user, 1),
            (self.ldap_user, 0),
        ]
        self.assert_element_count(
            expected, self.url_public, 'sodar-user-email-dropdown', 'class'
        )


class TestUserAppSettingsView(SiteUITestBase):
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


class TestUserListView(SiteUITestBase):
    def setUp(self):
        super().setUp()
        self.regular_user.first_name = 'Roger'
        self.regular_user.last_name = 'Larsen'
        self.regular_user.save()
        self.other_user = self.make_user('other_user')
        self.other_user.is_active = False
        self.other_user.save()
        self.url = reverse('userprofile:list')

    def assert_user_row_fields(self, row, user):
        user_profile_path = reverse(
            'userprofile:detail_public', kwargs={'user': user.sodar_uuid}
        )
        user_profile_href = (
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(1)')
            .find_element(By.TAG_NAME, 'a')
            .get_attribute('href')
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(1)').text,
            user.username,
        )
        self.assertEqual(
            urlsplit(user_profile_href).path,
            user_profile_path,
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text,
            user.first_name,
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text,
            user.last_name,
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text,
            user.email,
        )
        self.assertEqual(
            f'mailto:{user.email}',
            row.find_element(
                By.CSS_SELECTOR, 'td:nth-child(4) a'
            ).get_attribute('href'),
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(5)').text,
            str(user.is_active).lower(),
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(6)').text,
            localtime(user.date_joined).strftime('%Y-%m-%d %H:%M:%S'),
        )
        self.assertEqual(
            row.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text,
            str(user.sodar_uuid),
        )

    def test_table_content(self):
        """Test UserListView table content"""
        self.login_and_redirect(
            self.regular_user,
            self.url,
            '#sodar-up-ajax-user-list-table tr',
            'CSS_SELECTOR',
        )
        rows = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '#sodar-up-ajax-user-list-table tr',
        )
        self.assertEqual(len(rows), 3)
        self.assert_user_row_fields(
            rows[0],
            self.other_user,
        )
        self.assert_user_row_fields(
            rows[1],
            self.regular_user,
        )
        self.assert_user_row_fields(
            rows[2],
            self.superuser,
        )

    def test_table_pagination(self):
        """Test UserListView table pagination"""
        for i in range(10):
            self.make_user(f'temp_user{i}')
        self.login_and_redirect(
            self.regular_user,
            self.url,
            '#sodar-up-ajax-user-list-table tr',
            'CSS_SELECTOR',
        )
        rows = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '#sodar-up-ajax-user-list-table tr',
        )
        self.assertEqual(len(rows), 10)
        select_input = self.selenium.find_element(
            By.ID,
            'sodar-up-user-list-page-length',
        )
        select_input.click()
        select_input.find_element(
            By.CSS_SELECTOR,
            'option:nth-child(3)',
        ).click()
        rows = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '#sodar-up-ajax-user-list-table tr',
        )
        self.assertEqual(len(rows), 13)

    def test_table_filtering(self):
        """Test UserListView table filtering"""
        self.login_and_redirect(
            self.regular_user,
            self.url,
            '#sodar-up-ajax-user-list-table tr',
            'CSS_SELECTOR',
        )
        filter_input = self.selenium.find_element(
            By.ID,
            'sodar-up-user-list-filter',
        )
        filter_input.send_keys('other_u')
        rows = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '#sodar-up-ajax-user-list-table tr',
        )
        self.assertEqual(len(rows), 1)
        self.assert_user_row_fields(
            rows[0],
            self.other_user,
        )
