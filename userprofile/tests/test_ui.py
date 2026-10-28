"""UI tests for the userprofile app"""

from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import localtime

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.forms import APP_SETTING_DISABLE_LABEL
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import (
    SODARUserAdditionalEmailMixin,
    ProjectMixin,
    RoleAssignmentMixin,
    RoleMixin,
)
from projectroles.tests.base import SiteUITestBase


app_settings = AppSettingAPI()


# SODAR constants
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME_PR = 'projectroles'
UPDATE_BTN_ID = 'sodar-user-btn-update'
SETTING_BTN_ID = 'sodar-user-btn-settings'
EMAIL_ADD_BTN_ID = 'sodar-user-btn-email-add'


@override_settings(AUTH_LDAP_USERNAME_DOMAIN='EXAMPLE')
class TestUserDetailView(
    SODARUserAdditionalEmailMixin,
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    SiteUITestBase,
):
    """Tests for UserDetailView"""

    def setUp(self):
        super().setUp()
        super().init_roles()
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

    def test_project_list_absence(self):
        """Test absence of project list in private profile"""
        self.login_and_redirect(self.local_user, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-project-list-table')

    def test_project_list(self):
        """Test project list in public profile"""
        category = self.make_project('category', PROJECT_TYPE_CATEGORY, None)
        project = self.make_project('project', PROJECT_TYPE_PROJECT, category)
        self.make_assignment(category, self.local_user, self.role_owner)
        self.login_and_redirect(self.superuser, self.url_public)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CLASS_NAME, 'sodar-pr-project-list-item'
            )
        )
        project_rows = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-list-item'
        )
        self.assertEqual(len(project_rows), 2)
        self.selenium.find_element(
            By.CLASS_NAME, f'sodar-pr-project-list-item-{category.uuid}'
        )
        self.selenium.find_element(
            By.CLASS_NAME, f'sodar-pr-project-list-item-{project.uuid}'
        )

    def test_project_list_empty(self):
        """Test empty project list in public profile"""
        self.login_and_redirect(self.ldap_user, self.url_public)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(By.ID, 'sodar-pr-project-list-message')
        )
        project_list_msg = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-message'
        )
        self.assertTrue(project_list_msg.text != '')
        self.assertEqual(
            self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-project-list-item'
            ),
            [],
        )

    def test_project_list_star(self):
        """Test project list star default not saved"""
        category = self.make_project('category', PROJECT_TYPE_CATEGORY, None)
        project = self.make_project('project', PROJECT_TYPE_PROJECT, category)
        self.make_assignment(category, self.local_user, self.role_owner)
        self.make_assignment(category, self.ldap_user, self.role_delegate)
        self.assertEqual(
            app_settings.get(
                APP_NAME_PR, 'project_list_home_starred', user=self.ldap_user
            ),
            False,
        )
        app_settings.set(
            plugin_name=APP_NAME_PR,
            setting_name='project_star',
            value=True,
            project=project,
            user=self.ldap_user,
            validate=False,
        )

        def _project_rows_count(driver):
            project_rows = driver.find_elements(
                By.CLASS_NAME, 'sodar-pr-project-list-item'
            )
            return len(project_rows)

        self.login_and_redirect(self.ldap_user, self.url_public)
        WebDriverWait(self.selenium, 15).until(
            lambda x: _project_rows_count(x) == 2
        )
        button = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-link-star'
        )
        button.click()
        WebDriverWait(self.selenium, 15).until(
            lambda x: _project_rows_count(x) == 1
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-project-list-message')
        self.assertEqual(
            app_settings.get(
                APP_NAME_PR, 'project_list_home_starred', user=self.ldap_user
            ),
            False,
        )

    def test_back_button_from_user_list_view(self):
        """Test "Back" button in public profile from user list view"""
        url = reverse('userprofile:list')
        self.login_and_redirect(self.regular_user, url)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CSS_SELECTOR, '#sodar-up-ajax-user-list-table a:nth-child(1)'
            )
        )
        self.selenium.find_element(
            By.CSS_SELECTOR, '#sodar-up-ajax-user-list-table a:nth-child(1)'
        ).click()
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(By.ID, 'sodar-up-public-view-back-btn')
        )
        back_btn = self.selenium.find_element(
            By.ID, 'sodar-up-public-view-back-btn'
        )
        self.assertEqual(back_btn.text, 'Back')
        self.assertTrue(back_btn.get_attribute('href').endswith(url))

    def test_back_button_from_project_members_view(self):
        """Test "Back" button in public profile from project members view"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.regular_user, self.role_owner)
        url = reverse(
            'projectroles:roles', kwargs={'project': category.sodar_uuid}
        )
        self.login_and_redirect(self.regular_user, url)
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(
                By.CSS_SELECTOR, '#sodar-pr-role-list-table a:nth-child(1)'
            )
        )
        self.selenium.find_element(
            By.CSS_SELECTOR, '#sodar-pr-role-list-table a:nth-child(1)'
        ).click()
        WebDriverWait(self.selenium, 15).until(
            lambda x: x.find_element(By.ID, 'sodar-up-public-view-back-btn')
        )
        back_btn = self.selenium.find_element(
            By.ID, 'sodar-up-public-view-back-btn'
        )
        self.assertEqual(back_btn.text, 'Back')
        self.assertTrue(back_btn.get_attribute('href').endswith(url))

    def test_back_button_absence_in_private_profile(self):
        """Test "Back" button absence when viewing a private profile"""
        self.login_and_redirect(self.local_user, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-up-public-view-back-btn')


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
        """
        Assert UserListView table fields.

        :param row: selenium element for a table row
        :param user: User object corresponding to that row
        :raise: AssertionError if row fields are not as expected
        """
        cells = row.find_elements(By.TAG_NAME, 'td')
        if user.is_superuser:
            # Wait before icon is rendered
            WebDriverWait(cells[0], 15).until(
                lambda x: x.find_element(By.TAG_NAME, 'svg')
            )
            user_icon = (
                cells[0]
                .find_element(By.TAG_NAME, 'svg')
                .get_attribute('data-icon')
            )
            self.assertEqual(user_icon, 'mdi:shield-account')
        if not user.is_active:
            # Wait before icon is rendered
            WebDriverWait(cells[0], 15).until(
                lambda x: x.find_element(By.TAG_NAME, 'svg')
            )
            user_icon = (
                cells[0]
                .find_element(By.TAG_NAME, 'svg')
                .get_attribute('data-icon')
            )
            self.assertEqual(user_icon, 'mdi:account-off')
        table_href = (
            cells[0].find_element(By.TAG_NAME, 'a').get_attribute('href')
        )
        user_profile_link = reverse(
            'userprofile:detail_public',
            kwargs={'user': user.sodar_uuid},
        )
        self.assertTrue(table_href.endswith(user_profile_link))
        self.assertEqual(cells[0].text, user.username)
        self.assertEqual(cells[1].text, user.first_name)
        self.assertEqual(cells[2].text, user.last_name)
        self.assertEqual(cells[3].text, user.email)
        self.assertEqual(
            cells[3].find_element(By.TAG_NAME, 'a').get_attribute('href'),
            f'mailto:{user.email}',
        )
        self.assertEqual(
            cells[4].text,
            localtime(user.date_joined).strftime('%Y-%m-%d'),
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
        self.assert_user_row_fields(rows[0], self.other_user)
        self.assert_user_row_fields(rows[1], self.regular_user)
        self.assert_user_row_fields(rows[2], self.superuser)

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
        self.assert_user_row_fields(rows[0], self.other_user)
