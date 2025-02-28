"""UI tests for the tokens app"""

from datetime import timedelta

from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from knox.models import AuthToken

from selenium.webdriver.common.by import By

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_ui import UITestBase


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']

# Local constants
APP_NAME_PR = 'projectroles'


class TestUserTokenListView(UITestBase):
    """Tests for UserTokenListView"""

    def setUp(self):
        super().setUp()
        # Create users
        self.superuser = self.make_user('superuser', True)
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user', False)

        # Create tokens
        self.token = AuthToken.objects.create(
            self.regular_user, timedelta(days=5)
        )[0]
        self.token_no_expiry = AuthToken.objects.create(
            self.regular_user, None
        )[0]
        self.url = reverse('tokens:list')

    def test_create_button(self):
        """Test visibility of create button"""
        self.assertFalse(app_settings.get(APP_NAME_PR, 'site_read_only'))
        self.assert_element_exists(
            [self.superuser, self.regular_user],
            self.url,
            'sodar-tk-create-btn',
            True,
        )

    def test_create_button_read_only(self):
        """Test visibility of create button with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        self.assert_element_exists(
            [self.superuser], self.url, 'sodar-tk-create-btn', True
        )
        self.assert_element_exists(
            [self.regular_user], self.url, 'sodar-tk-create-btn', False
        )

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_create_button_restrict(self):
        """Test create button with restriction"""
        self.login_and_redirect(self.regular_user, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-tk-create-btn')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_create_button_restrict_role(self):
        """Test create button with restriction as user with role"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.regular_user, self.role_guest)
        self.login_and_redirect(self.regular_user, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-tk-create-btn')
        self.assertIsNone(elem.get_attribute('disabled'))

    @override_settings(TOKENS_CREATE_PROJECT_USER_RESTRICT=True)
    def test_create_button_restrict_superuser(self):
        """Test create button with restriction as superuser"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-tk-create-btn')
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_list_items(self):
        """Test visibility of items in token list"""
        expected = [(self.superuser, 0), (self.regular_user, 2)]
        self.assert_element_count(
            expected, self.url, 'sodar-tk-list-item', 'class'
        )
        self.assert_element_count(
            expected, self.url, 'sodar-tk-item-dropdown', 'class'
        )

    def test_list_items_read_only(self):
        """Test visibility of items in token list with site read-only mode"""
        app_settings.set(APP_NAME_PR, 'site_read_only', True)
        expected = [(self.superuser, 0), (self.regular_user, 2)]
        self.assert_element_count(
            expected, self.url, 'sodar-tk-list-item', 'class'
        )
        expected = [(self.superuser, 0), (self.regular_user, 0)]
        self.assert_element_count(
            expected, self.url, 'sodar-tk-item-dropdown', 'class'
        )

    def test_list_expiry(self):
        """Test token expiry dates in token list"""
        self.login_and_redirect(self.regular_user, self.url)
        items = self.selenium.find_elements(By.CLASS_NAME, 'sodar-tk-list-item')
        self.assertEqual(len(items), 2)
        expiry_time = timezone.localtime(self.token.expiry).strftime(
            '%Y-%m-%d %H:%M'
        )
        values = []
        for item in items:
            values.append(item.find_elements(By.TAG_NAME, 'td')[2].text)
        self.assertCountEqual(values, ['Never', expiry_time])
