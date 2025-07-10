"""UI tests for the projectroles app"""

import socket
import time
import uuid

from typing import Optional, Union
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import (
    SESSION_KEY,
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
)
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import QuerySet
from django.test import LiveServerTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait, Select

from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    SODARUser,
    SODAR_CONSTANTS,
    CAT_DELIMITER,
)
from projectroles.plugins import PluginAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    RemoteTargetMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
)
from projectroles.utils import build_secret


app_settings = AppSettingAPI()
plugin_api = PluginAPI()
User = auth.get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']

# Local constants
APP_NAME = 'projectroles'
PROJECT_LINK_IDS = [
    'sodar-pr-link-project-roles',
    'sodar-pr-link-project-update',
    'sodar-pr-link-project-create',
    'sodar-pr-link-project-star',
]
DEFAULT_WAIT_LOC = 'ID'
HEAD_INCLUDE = '<meta name="keywords" content="SODAR Core">'
REMOTE_SITE_NAME = 'Remote Site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_DESC = 'New description'
REMOTE_SITE_SECRET = build_secret()
PROJECT_SELECT_CSS = 'div[id="div_id_type"] div select[id="id_type"]'
PROJECT_SETTING_ID = 'div_id_settings.example_project_app.project_int_setting'
CATEGORY_SETTING_ID = (
    'div_id_settings.example_project_app.category_bool_setting'
)
PUBLIC_ACCESS_ID = 'id_public_access'
REMOTE_SITE_UUID = uuid.uuid4()
REMOTE_SITE_ID = f'id_remote_site.{REMOTE_SITE_UUID}'
CUSTOM_READ_ONLY_MSG = 'This is a custom site read-only mode message.'


class SeleniumSetupMixin:
    """Mixin for setting up selenium for a test class"""

    #: Selenium Chrome options from settings
    chrome_options = getattr(
        settings,
        'PROJECTROLES_TEST_UI_CHROME_OPTIONS',
        [
            'headless=new',
            'no-sandbox',  # For Gitlab-CI compatibility
            'disable-dev-shm-usage',  # For testing stability
        ],
    )

    #: Selenium window size from settings
    window_size = getattr(
        settings, 'PROJECTROLES_TEST_UI_WINDOW_SIZE', (1400, 1000)
    )

    #: UI test wait time from settings
    wait_time = getattr(settings, 'PROJECTROLES_TEST_UI_WAIT_TIME', 30)

    def set_up_selenium(self):
        socket.setdefaulttimeout(60)  # To get around Selenium hangups
        # Init Chrome
        options = webdriver.ChromeOptions()
        for arg in self.chrome_options:
            options.add_argument(arg)
        self.selenium = webdriver.Chrome(options=options)
        # Prevent ElementNotVisibleException
        self.selenium.set_window_size(self.window_size[0], self.window_size[1])


class LiveUserMixin:
    """Mixin for creating users to work with LiveServerTestCase"""

    @classmethod
    def make_user(cls, user_name: str, superuser: bool = False) -> SODARUser:
        """Make user, superuser if superuser=True"""
        kwargs = {
            'username': user_name,
            'password': 'password',
            'email': f'{user_name}@example.com',
            'is_active': True,
        }
        if superuser:
            user = User.objects.create_superuser(**kwargs)
        else:
            user = User.objects.create_user(**kwargs)
        user.save()
        return user


class UITestMixin:
    """Helper mixin for UI tests"""

    def build_selenium_url(self, url: str = '') -> str:
        """Build absolute URL to work with Selenium"""
        # NOTE: Chrome v77 refuses to accept cookies for "localhost" (see #337)
        return '{}{}'.format(
            self.live_server_url.replace('localhost', '127.0.0.1'), url
        )

    def login_and_redirect(
        self,
        user: SODARUser,
        url: str,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Login with Selenium by setting a cookie, wait for redirect to given URL.

        If PROJECTROLES_TEST_UI_LEGACY_LOGIN=True, use legacy UI login method.

        :param user: SODARUser object
        :param url: URL to redirect to (string)
        :param wait_elem: Wait for existence of an element (string, optional)
        :param wait_loc: Locator of optional wait element (string, corresponds
                         to selenium "By" class members)
        """
        # Legacy login mode
        if getattr(settings, 'PROJECTROLES_TEST_UI_LEGACY_LOGIN', False):
            return self.login_and_redirect_with_ui(
                user, url, wait_elem, wait_loc
            )
        # Cookie login mode
        self.selenium.get(self.build_selenium_url(reverse('login')))
        # Wait for page load to prevent RemoteDisconnected
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, 'sodar-content-container'))
        )

        session = SessionStore()
        session[SESSION_KEY] = user.id
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[1]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()
        cookie = {
            'name': settings.SESSION_COOKIE_NAME,
            'value': session.session_key,
            'path': '/',
            'domain': self.build_selenium_url().split('//')[1].split(':')[0],
        }
        self.selenium.add_cookie(cookie)
        self.selenium.get(self.build_selenium_url(url))

        # Wait for redirect
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (By.ID, 'sodar-navbar-user-dropdown')
            )
        )
        # Wait for optional element
        if wait_elem:
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.presence_of_element_located(
                    (getattr(By, wait_loc), wait_elem)
                )
            )

    # NOTE: Used if PROJECTROLES_TEST_UI_LEGACY_LOGIN is set True
    def login_and_redirect_with_ui(
        self,
        user: SODARUser,
        url: str,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Login with Selenium and wait for redirect to given URL.

        :param user: User object
        :param url: URL to redirect to (string)
        :param wait_elem: Wait for existence of an element (string, optional)
        :param wait_loc: Locator of optional wait element (string, corresponds
                         to selenium "By" class members)
        """
        self.selenium.get(self.build_selenium_url('/'))

        # Logout (if logged in)
        try:
            user_button = self.selenium.find_element(
                By.ID, 'sodar-navbar-user-dropdown'
            )
            user_button.click()
            # Wait for element to be visible
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.presence_of_element_located(
                    (By.ID, 'sodar-navbar-user-legend')
                )
            )
            try:
                signout_button = self.selenium.find_element(
                    By.ID, 'sodar-navbar-link-logout'
                )
                signout_button.click()
                # Wait for redirect
                WebDriverWait(self.selenium, self.wait_time).until(
                    ec.presence_of_element_located((By.ID, 'sodar-form-login'))
                )
            except NoSuchElementException:
                pass
        except NoSuchElementException:
            pass

        # Login
        self.selenium.get(self.build_selenium_url(url))
        # Submit user data into form
        field_user = self.selenium.find_element(By.ID, 'sodar-login-username')
        # field_user.send_keys(user.username)
        field_user.send_keys(user.username)
        field_pass = self.selenium.find_element(By.ID, 'sodar-login-password')
        field_pass.send_keys('password')
        self.selenium.find_element(By.ID, 'sodar-login-submit').click()
        # Wait for redirect
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (By.ID, 'sodar-navbar-user-dropdown')
            )
        )
        # Wait for optional element
        if wait_elem:
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.presence_of_element_located(
                    (getattr(By, wait_loc), wait_elem)
                )
            )

    def assert_element_exists(
        self,
        users: Union[list[SODARUser], QuerySet[SODARUser]],
        url: str,
        element_id: str,
        exists: bool,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Assert existence of element on webpage based on logged user.

        :param users: User objects to test (list)
        :param url: URL to test (string)
        :param element_id: ID of element (string)
        :param exists: Whether element should or should not exist (boolean)
        :param wait_elem: Wait for existence of an element (string, optional)
        :param wait_loc: Locator of optional wait element (string, corresponds
                         to selenium "By" class members)
        """
        for user in users:
            self.login_and_redirect(user, url, wait_elem, wait_loc)
            if exists:
                self.assertIsNotNone(
                    self.selenium.find_element(By.ID, element_id)
                )
            else:
                with self.assertRaises(NoSuchElementException):
                    self.selenium.find_element(By.ID, element_id)

    def assert_element_count(
        self,
        expected: list[tuple],
        url: str,
        search_string: str,
        attribute: str = 'id',
        path: str = '//',
        exact: bool = False,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Assert count of elements containing specified id or class based on
        the logged user.

        :param expected: List of tuples with user (string), count (int)
        :param url: URL to test (string)
        :param search_string: ID substring of element (string)
        :param attribute: Attribute to search for (string, default=id)
        :param path: Path for searching (string, default="//")
        :param exact: Exact match if True (boolean, default=False)
        :param wait_elem: Wait for existence of an element (string, optional)
        :param wait_loc: Locator of optional wait element (string, corresponds
                         to selenium "By" class members)
        """
        for e in expected:
            expected_user = e[0]  # Just to clarify code
            self.login_and_redirect(expected_user, url, wait_elem, wait_loc)
            xpath = '{}*[@{}="{}"]' if exact else '{}*[contains(@{}, "{}")]'
            expected_count = e[1]
            if expected_count > 0:
                self.assertEqual(
                    len(
                        self.selenium.find_elements(
                            By.XPATH,
                            xpath.format(path, attribute, search_string),
                        )
                    ),
                    expected_count,
                    f'expected_user={expected_user}',
                )
            else:
                with self.assertRaises(NoSuchElementException):
                    self.selenium.find_element(
                        By.XPATH,
                        xpath.format(path, attribute, search_string),
                    )

    def assert_element_set(
        self,
        expected: list[tuple],
        all_elements: list[str],
        url: str,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Assert existence of expected elements webpage based on logged user, as
        well as non-existence non-expected elements.

        :param expected: List of tuples with user (string), elements (list)
        :param all_elements: All possible elements in the set (list of strings)
        :param url: URL to test (string)
        :param wait_elem: Wait for existence of an element (string, optional)
        :param wait_loc: Locator of optional wait element (string, corresponds
                         to selenium "By" class members)
        """
        for e in expected:
            user = e[0]
            elements = e[1]
            self.login_and_redirect(user, url, wait_elem, wait_loc)
            for element in elements:
                self.assertIsNotNone(self.selenium.find_element(By.ID, element))
            not_expected = list(set(all_elements) ^ set(elements))
            for n in not_expected:
                with self.assertRaises(NoSuchElementException):
                    self.selenium.find_element(By.ID, n)

    def assert_element_active(
        self,
        user: SODARUser,
        element_id: str,
        all_elements: list[str],
        url: str,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Assert the "active" status of an element based on logged user as well
        as unset status of other elements.

        :param user: SODARUser for logging in
        :param element_id: ID of element to test (string)
        :param all_elements: All possible elements in the set (list of strings)
        :param url: URL to test (string)
        :param wait_elem: Wait for existence of an element (string, optional)
        :param wait_loc: Locator of optional wait element (string, corresponds
                         to selenium "By" class members)
        """
        self.login_and_redirect(user, url, wait_elem, wait_loc)
        # Wait for element to be present (sometimes this is too slow)
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, element_id))
        )

        element = self.selenium.find_element(By.ID, element_id)
        self.assertIsNotNone(element)
        self.assertIn('active', element.get_attribute('class'))
        not_expected = [e for e in all_elements if e != element_id]
        for n in not_expected:
            element = self.selenium.find_element(By.ID, n)
            self.assertIsNotNone(element)
            self.assertNotIn('active', element.get_attribute('class'))

    def assert_displayed(self, by: str, value: str, expected: bool):
        """
        Assert element is or isn't displayed. Assumes user to be logged in.

        :param by: Selenium By selector
        :param value: Value for selecting element
        :param expected: Boolean
        """
        elem = self.selenium.find_element(by, value)
        self.assertEqual(elem.is_displayed(), expected)


class UITestBase(
    SeleniumSetupMixin,
    LiveUserMixin,
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    UITestMixin,
    LiveServerTestCase,
):
    """Base class for UI tests"""

    def setUp(self):
        # Set up Selenium
        self.set_up_selenium()
        # Init roles
        self.init_roles()

        # Init users
        self.superuser = self.make_user('admin', True)
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_delegate_cat = self.make_user('user_delegate_cat')
        self.user_contributor_cat = self.make_user('user_contributor_cat')
        self.user_guest_cat = self.make_user('user_guest_cat')
        self.user_viewer_cat = self.make_user('user_viewer_cat')
        self.user_finder_cat = self.make_user('user_finder_cat')
        self.user_owner = self.make_user('user_owner')
        self.user_delegate = self.make_user('user_delegate')
        self.user_contributor = self.make_user('user_contributor')
        self.user_guest = self.make_user('user_guest')
        self.user_viewer = self.make_user('user_viewer')
        self.user_no_roles = self.make_user('user_no_roles')

        # Init category and project
        self.category = self.make_project(
            title='TestCategory', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        self.project = self.make_project(
            title='TestProject',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
        )

        # Init role assignments
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.delegate_as_cat = self.make_assignment(
            self.category, self.user_delegate_cat, self.role_delegate
        )
        self.contributor_as_cat = self.make_assignment(
            self.category, self.user_contributor_cat, self.role_contributor
        )
        self.guest_as_cat = self.make_assignment(
            self.category, self.user_guest_cat, self.role_guest
        )
        self.viewer_as_cat = self.make_assignment(
            self.category, self.user_viewer_cat, self.role_viewer
        )
        self.finder_as_cat = self.make_assignment(
            self.category, self.user_finder_cat, self.role_finder
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.delegate_as = self.make_assignment(
            self.project, self.user_delegate, self.role_delegate
        )
        self.contributor_as = self.make_assignment(
            self.project, self.user_contributor, self.role_contributor
        )
        self.guest_as = self.make_assignment(
            self.project, self.user_guest, self.role_guest
        )
        self.viewer_as = self.make_assignment(
            self.category, self.user_viewer, self.role_viewer
        )

    def tearDown(self):
        # Shut down Selenium
        self.selenium.quit()
        super().tearDown()


class TestBaseTemplate(UITestBase):
    """Tests for the base project template"""

    def test_admin_link(self):
        """Test Dajngo admin link visibility according to user permissions"""
        expected_true = [self.superuser]
        expected_false = [
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
        ]
        url = reverse('home')
        elem_id = 'sodar-navbar-link-admin'
        self.assert_element_exists(expected_true, url, elem_id, True)
        self.assert_element_exists(expected_false, url, elem_id, False)

    def test_admin_link_modal(self):
        """Test Django admin warning modal opening"""
        self.login_and_redirect(self.superuser, reverse('home'))
        modal = self.selenium.find_element(By.ID, 'sodar-modal')
        self.assertEqual(modal.is_displayed(), False)
        # Open dropdown and click link
        self.selenium.find_element(By.ID, 'sodar-navbar-user-dropdown').click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, 'sodar-navbar-link-admin'))
        )
        link = self.selenium.find_element(By.ID, 'sodar-navbar-link-admin')
        link.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (By.ID, 'sodar-pr-admin-warning-modal-content')
            )
        )
        self.assertEqual(modal.is_displayed(), True)


class TestHomeView(UITestBase):
    """Tests for the home view and project list UI"""

    #: Home view URL
    url = reverse('home')

    #: Arguments for waiting for the list to get poplulated on the client side
    wait_kwargs = {
        'wait_elem': 'sodar-pr-project-list-item',
        'wait_loc': 'CLASS_NAME',
    }

    #: Arguments for populating an empty list with a message
    wait_kwargs_empty = {
        'wait_elem': 'sodar-pr-project-list-message',
        'wait_loc': 'ID',
    }

    def _get_item_vis_count(self) -> int:
        return len(
            [
                e
                for e in self.selenium.find_elements(
                    By.CLASS_NAME, 'sodar-pr-project-list-item'
                )
                if e.get_attribute('style') != 'display: none;'
            ]
        )

    def _get_list_item(self, project: Project) -> WebElement:
        return self.selenium.find_element(
            By.XPATH,
            f'//tr[contains(@class, "sodar-pr-project-list-item '
            f'sodar-pr-project-list-item-{project.type.lower()}") and '
            f'@data-uuid="{project.sodar_uuid}"]',
        )

    def _get_project_row(self, project: Project) -> WebElement:
        """Return table row for specificed project"""
        return self.selenium.find_element(
            By.ID, f'sodar-pr-project-list-item-{project.sodar_uuid}'
        )

    def _wait_for_async_requests(self):
        """Wait for async requests to finish"""
        WebDriverWait(self.selenium, self.wait_time).until_not(
            ec.presence_of_element_located(
                (By.CLASS_NAME, 'sodar-pr-project-list-load-icon')
            )
        )

    def setUp(self):
        super().setUp()
        self.url = reverse('home')
        self.wait_kwargs = {
            'wait_elem': 'sodar-pr-project-list-item',
            'wait_loc': 'CLASS_NAME',
        }
        self.wait_kwargs_empty = {
            'wait_elem': 'sodar-pr-project-list-message',
            'wait_loc': 'ID',
        }

    def test_project_list_items(self):
        """Test visibility of project list items"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 2),
            (self.user_finder_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer_cat, 2),
        ]
        elem_id = 'sodar-pr-project-list-item'
        self.assert_element_count(
            expected, self.url, elem_id, **self.wait_kwargs
        )
        self.assert_element_count(
            [(self.user_no_roles, 0)],
            self.url,
            elem_id,
            **self.wait_kwargs_empty,
        )

    def test_project_list_items_public_guest(self):
        """Test project list items with public guest access"""
        self.project.set_public_access(self.role_guest)
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 2),
            (self.user_finder_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer, 2),
            (self.user_no_roles, 2),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-pr-project-list-item', **self.wait_kwargs
        )

    def test_project_list_items_public_viewer(self):
        """Test project list items with public viewer access"""
        self.project.set_public_access(self.role_viewer)
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 2),
            (self.user_finder_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer, 2),
            (self.user_no_roles, 2),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-pr-project-list-item', **self.wait_kwargs
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_list_items_public_guest_anon(self):
        """Test project list items with public guest access and anonymous user"""
        self.project.set_public_access(self.role_guest)
        self.selenium.get(self.build_selenium_url(self.url))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, 'sodar-pr-project-list-item')
            )
        )
        self.assertEqual(self._get_item_vis_count(), 2)
        links = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-link'
        )
        self.assertEqual(len(links), 1)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_list_items_public_viewer_anon(self):
        """Test project list items with public viewer access and anonymous user"""
        self.project.set_public_access(self.role_viewer)
        self.selenium.get(self.build_selenium_url(self.url))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, 'sodar-pr-project-list-item')
            )
        )
        self.assertEqual(self._get_item_vis_count(), 2)
        links = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-link'
        )
        self.assertEqual(len(links), 1)

    def test_project_list_links_member(self):
        """Test project links as regular member"""
        self.login_and_redirect(self.user_guest, self.url, **self.wait_kwargs)
        elem = self._get_list_item(self.category)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-link')
        )
        elem = self._get_list_item(self.project)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-link')
        )
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-findable')

    def test_project_list_links_finder(self):
        """Test project links as finder"""
        self.login_and_redirect(
            self.user_finder_cat, self.url, **self.wait_kwargs
        )
        elem = self._get_list_item(self.category)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-link')
        )
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-findable')
        # Project is present but it is not a link
        elem = self._get_list_item(self.project)
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-link')
        # Link to parent project is found
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-project-findable')
        )

    def test_project_list_filter(self):
        """Test filtering project list items"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self.assertEqual(self._get_item_vis_count(), 2)
        f_input = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-filter'
        )
        f_input.send_keys('project')
        self.assertEqual(self._get_item_vis_count(), 1)

    def test_project_list_filter_trim(self):
        """Test filtering project list items with trimming for spaces"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self.assertEqual(self._get_item_vis_count(), 2)
        f_input = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-filter'
        )
        f_input.send_keys(' project  ')
        self.assertEqual(self._get_item_vis_count(), 1)

    def test_project_list_star(self):
        """Test project list star filter"""
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user_owner
            ),
            False,
        )
        app_settings.set(
            plugin_name=APP_NAME,
            setting_name='project_star',
            value=True,
            project=self.project,
            user=self.user_owner,
            validate=False,
        ),
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self.assertEqual(self._get_item_vis_count(), 2)
        button = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-link-star'
        )
        button.click()
        self.assertEqual(self._get_item_vis_count(), 1)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-project-list-message')
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user_owner
            ),
            True,
        )

    def test_project_list_star_no_project(self):
        """Test project list star filter with no starred project"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self.assertEqual(self._get_item_vis_count(), 2)
        button = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-link-star'
        )
        self.assertFalse(button.is_enabled())

    def test_project_list_filter_star(self):
        """Test toggling star with filter enabled"""
        app_settings.set(
            plugin_name=APP_NAME,
            setting_name='project_star',
            value=True,
            project=self.category,
            user=self.user_owner,
            validate=False,
        ),
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self.assertEqual(self._get_item_vis_count(), 2)
        f_input = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-filter'
        )
        f_input.send_keys('testproject')
        self.assertEqual(self._get_item_vis_count(), 1)
        self.assertEqual(self._get_list_item(self.project).is_displayed(), True)
        with self.assertRaises(NoSuchElementException):
            self._get_list_item(self.category)
        button = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-link-star'
        )
        button.click()
        self.assertEqual(self._get_item_vis_count(), 1)
        with self.assertRaises(NoSuchElementException):
            self._get_list_item(self.project)
        self.assertEqual(
            self._get_list_item(self.category).is_displayed(), True
        )
        self.assertEqual(f_input.get_attribute('value'), '')

    def test_project_list_title(self):
        """Test project list title rendering"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        icon = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-title-container'
        ).find_element(By.CLASS_NAME, 'iconify')
        self.assertEqual(icon.get_attribute('data-icon'), 'mdi:cube')
        link_html = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-title'
        ).find_element(By.TAG_NAME, 'a')
        expected = (
            self.category.title
            + CAT_DELIMITER
            + f'<strong>{self.project.title}</strong>'
        )
        self.assertEqual(link_html.get_attribute('innerHTML'), expected)
        # Assert no extra icons are present
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-starred')
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-archive')
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-block')
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-public')
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-findable')
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-stats')

    def test_project_list_title_no_highlight(self):
        """Test project list title rendering with no highlight"""
        app_settings.set(
            APP_NAME, 'project_list_highlight', False, user=self.user_owner
        )
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        link_html = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-title'
        ).find_element(By.TAG_NAME, 'a')
        self.assertEqual(
            link_html.get_attribute('innerHTML'), self.project.full_title
        )

    def test_project_list_title_category(self):
        """Test project list title rendering with category"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.category)
        icon = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-title-container'
        ).find_element(By.CLASS_NAME, 'iconify')
        self.assertEqual(icon.get_attribute('data-icon'), 'mdi:rhombus-split')
        link_html = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-title'
        ).find_element(By.TAG_NAME, 'a')
        self.assertEqual(
            link_html.get_attribute('innerHTML'), self.category.full_title
        )

    def test_project_list_title_category_highlight(self):
        """Test project list title rendering with category and highlight"""
        sub_cat = self.make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(sub_cat, self.user_owner, self.role_owner)
        app_settings.set(
            APP_NAME, 'project_list_highlight', True, user=self.user_owner
        )
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(sub_cat)
        link_html = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-title'
        ).find_element(By.TAG_NAME, 'a')
        # No highlight should be applied
        self.assertEqual(
            link_html.get_attribute('innerHTML'), sub_cat.full_title
        )

    def test_project_list_title_star(self):
        """Test project list title rendering with starred project"""
        app_settings.set(
            APP_NAME,
            'project_star',
            True,
            project=self.project,
            user=self.user_owner,
        )
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-starred')
        )

    def test_project_list_title_archive(self):
        """Test project list title rendering with archived project"""
        self.project.archive = True
        self.project.save()
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-archive')
        )

    def test_project_list_title_block(self):
        """Test project list title rendering with project access block"""
        app_settings.set(
            APP_NAME, 'project_access_block', True, project=self.project
        )
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        # Project is present but it is not a link
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-link')
        # Blocked icon should be visible
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-blocked')
        )
        # Findable icon should not be visible even with access disabled
        with self.assertRaises(NoSuchElementException):
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-findable')

    def test_project_list_title_block_superuser(self):
        """Test project list title with project access block as superuser"""
        app_settings.set(
            APP_NAME, 'project_access_block', True, project=self.project
        )
        self.login_and_redirect(self.superuser, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        # Link should be available for superuser
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-link')
        )
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-blocked')
        )

    def test_project_list_title_public(self):
        """Test project list title rendering with public guest access"""
        self.project.set_public_access(self.role_guest)
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.project)
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-public')
        )

    def test_project_list_title_category_public_stats(self):
        """Test project list title rendering with category_public_stats"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.category)
        title = row.find_element(
            By.CLASS_NAME, 'sodar-pr-project-list-title-td'
        )
        self.assertIsNotNone(
            title.find_element(By.CLASS_NAME, 'sodar-pr-project-stats')
        )

    def test_project_list_custom_cols(self):
        """Test rendering custom columns"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self._wait_for_async_requests()
        row = self._get_project_row(self.project)
        cols = row.find_elements(By.CLASS_NAME, 'sodar-pr-project-list-custom')
        self.assertEqual(len(cols), 2)
        for c in cols:
            self.assertEqual(c.get_attribute('innerHTML'), '0')

    def test_project_list_custom_cols_category(self):
        """Test rendering custom columns with category"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        row = self._get_project_row(self.category)
        cols = row.find_elements(By.CLASS_NAME, 'sodar-pr-project-list-custom')
        self.assertEqual(len(cols), 0)

    def test_project_list_role_col_owner(self):
        """Test rendering role column as owner"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self._wait_for_async_requests()
        row = self._get_project_row(self.project)
        col = row.find_element(By.CLASS_NAME, 'sodar-pr-project-list-role')
        self.assertEqual(
            col.get_attribute('class'), 'sodar-pr-project-list-role'
        )
        self.assertEqual(col.get_attribute('innerHTML'), 'Owner')

    def test_project_list_role_col_superuser(self):
        """Test rendering role column as superuser"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kwargs)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.CLASS_NAME, 'sodar-pr-project-list-role'
            )

    def test_project_list_role_col_category_inherit(self):
        """Test rendering role column with inherited role"""
        # Owner user has no role in parent category
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self._wait_for_async_requests()
        row = self._get_project_row(self.category)
        col = row.find_element(By.CLASS_NAME, 'sodar-pr-project-list-role')
        self.assertEqual(
            col.get_attribute('class'), 'sodar-pr-project-list-role text-muted'
        )
        self.assertEqual(col.get_attribute('innerHTML'), 'N/A')

    def test_project_list_paginate_disabled(self):
        """Test project list pagination with pagination disabled"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        elem = self.selenium.find_element(By.CLASS_NAME, 'dataTables_paginate')
        self.assertEqual(elem.is_displayed(), False)

    def test_project_list_paginate_enabled(self):
        """Test project list pagination with pagination enabled"""
        # Create additional categories to fill first page
        for i in range(1, 10):
            c = self.make_project(
                f'Additional Category {i}', PROJECT_TYPE_CATEGORY, None
            )
            self.make_assignment(c, self.user_owner, self.role_owner)
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        elem = self.selenium.find_element(By.CLASS_NAME, 'dataTables_paginate')
        self.assertEqual(elem.is_displayed(), True)

    def test_project_list_paginate_update(self):
        """Test project list pagination updating on second page"""
        for i in range(1, 10):
            c = self.make_project(
                f'Additional Category {i}', PROJECT_TYPE_CATEGORY, None
            )
            self.make_assignment(c, self.user_owner, self.role_owner)
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self._wait_for_async_requests()
        # Only category should be visible
        self.assertIsNotNone(self._get_project_row(self.category))
        with self.assertRaises(NoSuchElementException):
            self._get_project_row(self.project)

        # Navigate to page 2
        btn = self.selenium.find_element(By.XPATH, '//a[@data-dt-idx="3"]')
        btn.click()
        WebDriverWait(self.selenium, 15).until(
            ec.presence_of_element_located(
                (By.ID, f'sodar-pr-project-list-item-{self.project.sodar_uuid}')
            )
        )
        # Only project should be visible
        with self.assertRaises(NoSuchElementException):
            self._get_project_row(self.category)
        row = self._get_project_row(self.project)

        # Ensure extra columns were updated on previously hidden elements
        cols = row.find_elements(By.CLASS_NAME, 'sodar-pr-project-list-custom')
        self.assertEqual(len(cols), 2)
        for c in cols:
            self.assertEqual(c.get_attribute('innerHTML'), '0')
        col = row.find_element(By.CLASS_NAME, 'sodar-pr-project-list-role')
        self.assertEqual(
            col.get_attribute('class'), 'sodar-pr-project-list-role'
        )
        self.assertEqual(col.get_attribute('innerHTML'), 'Owner')

    def test_project_list_paginate_control(self):
        """Test project list pagination control"""
        for i in range(1, 10):
            c = self.make_project(
                f'Additional Category {i}', PROJECT_TYPE_CATEGORY, None
            )
            self.make_assignment(c, self.user_owner, self.role_owner)
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_pagination', user=self.user_owner
            ),
            10,
        )

        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        project_elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-list-item'
        )
        self.assertEqual(len(project_elems), 10)
        with self.assertRaises(NoSuchElementException):
            self._get_project_row(self.project)

        elem = Select(
            self.selenium.find_element(
                By.ID, 'sodar-pr-project-list-page-length'
            )
        )
        elem.select_by_value('25')
        WebDriverWait(self.selenium, 15).until(
            ec.presence_of_element_located(
                (By.ID, f'sodar-pr-project-list-item-{self.project.sodar_uuid}')
            )
        )
        project_elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-list-item'
        )
        self.assertEqual(len(project_elems), 11)
        time.sleep(1)  # Wait just in case
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_pagination', user=self.user_owner
            ),
            25,
        )

    def test_link_create_toplevel(self):
        """Test project creation link visibility"""
        expected_true = [self.superuser]
        expected_false = [
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
        ]
        self.assert_element_exists(
            expected_true, self.url, 'sodar-pr-link-home-project-create', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-pr-link-home-project-create', False
        )

    @override_settings(PROJECTROLES_INLINE_HEAD_INCLUDE=HEAD_INCLUDE)
    def test_inline_head_include_enabled(self):
        """Test visibility of inline head include from env variables"""
        self.login_and_redirect(self.user_owner, self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.XPATH, '//meta[@name="keywords"]')
        )

    def test_inline_head_include_disabled(self):
        """Test absence of inline head include when not set"""
        self.login_and_redirect(self.user_owner, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.XPATH, '//meta[@name="keywords"]')

    def test_read_only_alert_disabled(self):
        """Test site read-only mode alert with mode disabled"""
        self.assertFalse(app_settings.get(APP_NAME, 'site_read_only'))
        self.login_and_redirect(self.user_owner, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-alert-site-read-only')

    def test_read_only_alert_enabled(self):
        """Test site read-only mode alert with mode enabled"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        self.login_and_redirect(self.user_owner, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-alert-site-read-only')
        self.assertIsNotNone(elem)
        self.assertNotEqual(elem.text, CUSTOM_READ_ONLY_MSG)

    @override_settings(PROJECTROLES_READ_ONLY_MSG=CUSTOM_READ_ONLY_MSG)
    def test_read_only_alert_custom(self):
        """Test site read-only mode alert with custom message"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        self.login_and_redirect(self.user_owner, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-alert-site-read-only')
        self.assertIsNotNone(elem)
        self.assertEqual(elem.text, CUSTOM_READ_ONLY_MSG)

    def test_read_only_alert_disable(self):
        """Test site read-only mode disabling enabled alert"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        self.login_and_redirect(self.user_owner, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-alert-site-read-only')
        self.assertIsNotNone(elem)
        self.assertIn('alert-danger', elem.get_attribute('class'))
        self.assertNotIn('alert-success', elem.get_attribute('class'))
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.TAG_NAME, 'a')

        app_settings.set(APP_NAME, 'site_read_only', False)
        WebDriverWait(self.selenium, 15).until(
            ec.presence_of_element_located(
                (By.CLASS_NAME, 'sodar-alert-site-read-only-updated')
            )
        )
        self.assertNotIn('alert-danger', elem.get_attribute('class'))
        self.assertIn('alert-success', elem.get_attribute('class'))
        self.assertIsNotNone(elem.find_element(By.TAG_NAME, 'a'))


class TestProjectSidebar(ProjectInviteMixin, RemoteTargetMixin, UITestBase):
    """Tests for the project sidebar"""

    def setUp(self):
        super().setUp()
        self.sidebar_ids = [
            'sodar-pr-nav-project-detail',
            'sodar-pr-nav-project-roles',
            'sodar-pr-nav-project-update',
        ]
        # Add app plugin navs
        for p in plugin_api.get_active_plugins():
            self.sidebar_ids.append(f'sodar-pr-nav-app-plugin-{p.name}')

    def test_render_detail(self):
        """Test visibility of sidebar in the project_detail view"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-sidebar', True
        )

    def test_render_home(self):
        """Test visibility of sidebar in the home view"""
        url = reverse('home')
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-sidebar', True
        )

    def test_app_links(self):
        """Test visibility of app links"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = [(self.superuser, len(plugin_api.get_active_plugins()))]
        self.assert_element_count(expected, url, 'sodar-pr-nav-app-plugin')

    @override_settings(PROJECTROLES_HIDE_PROJECT_APPS=['timeline'])
    def test_app_links_hide(self):
        """Test visibility of app links with timeline hidden"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = [
            (self.superuser, len(plugin_api.get_active_plugins()) - 1),
            (self.user_owner, len(plugin_api.get_active_plugins()) - 1),
        ]
        self.assert_element_count(expected, url, 'sodar-pr-nav-app-plugin')

    def test_update_link(self):
        """Test visibility of update link"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        expected_false = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-nav-project-update', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-update', False
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-alt-link-project-update', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-update', False
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_update_link_target(self):
        """Test visibility of update link as target"""
        # Set up site as target
        self.set_up_as_target(projects=[self.category, self.project])

        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        expected_false = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

        self.assert_element_exists(
            expected_true, url, 'sodar-pr-nav-project-update', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-update', False
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-alt-link-project-update', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-update', False
        )

    def test_create_link(self):
        """Test visibility of create link"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
        ]
        expected_false = [
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )

        self.assert_element_exists(
            expected_true, url, 'sodar-pr-nav-project-create', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-create', False
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-alt-link-project-create', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-create', False
        )

    @override_settings(PROJECTROLES_DISABLE_CATEGORIES=True)
    def test_create_link_disable_categories(self):
        """Test visibility of create link with categories disabled"""
        expected_true = [self.superuser]
        expected_false = [
            self.user_owner,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

        self.assert_element_exists(
            expected_true, url, 'sodar-pr-nav-project-create', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-create', False
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-alt-link-project-create', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-create', False
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_create_link_target_remote(self):
        """Test visibility of create link as target under a remote category"""
        # Set up site as target
        self.set_up_as_target(projects=[self.category, self.project])

        expected_false = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )

        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-create', False
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-create', False
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_create_link_target_local(self):
        """Test visibility of create link as target under a local category"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
        ]
        expected_false = [
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )

        self.assert_element_exists(
            expected_true, url, 'sodar-pr-nav-project-create', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-create', False
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-alt-link-project-create', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-create', False
        )

    @override_settings(
        PROJECTROLES_SITE_MODE=SITE_MODE_TARGET,
        PROJECTROLES_TARGET_CREATE=False,
    )
    def test_create_link_target_disable(self):
        """Test visibility of create link as target with creation not allowed"""
        self.set_up_as_target(projects=[self.category, self.project])
        expected_false = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-nav-project-create', False
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-pr-alt-link-project-create', False
        )

    def test_link_active_detail(self):
        """Test active status of link on the project_detail page"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_active(
            self.superuser, 'sodar-pr-nav-project-detail', self.sidebar_ids, url
        )

    def test_link_active_role_list(self):
        """Test active status of link on the project roles page"""
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:roles',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )

    def test_link_active_role_create(self):
        """Test active status of link on the role creation page"""
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:role_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )

    def test_link_active_role_update(self):
        """Test active status of link on the role update page"""
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:role_update',
                kwargs={'roleassignment': self.contributor_as.sodar_uuid},
            ),
        )

    def test_link_active_role_delete(self):
        """Test active status of link on the role deletion page"""
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:role_delete',
                kwargs={'roleassignment': self.contributor_as.sodar_uuid},
            ),
        )

    def test_link_active_role_invites(self):
        """Test active status of link on the invites page"""
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:invites',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )

    def test_link_active_role_invite_create(self):
        """Test active status of link on the invite create page"""
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:invite_create',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )

    def test_link_active_role_invite_resend(self):
        """Test active status of link on the invite resend page"""
        invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:invite_resend',
                kwargs={'projectinvite': invite.sodar_uuid},
            ),
        )

    def test_link_active_role_invite_revoke(self):
        """Test active status of link on the invite revoke page"""
        invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        self.assert_element_active(
            self.superuser,
            'sodar-pr-nav-project-roles',
            self.sidebar_ids,
            reverse(
                'projectroles:invite_revoke',
                kwargs={'projectinvite': invite.sodar_uuid},
            ),
        )

    def test_link_active_update(self):
        """Test active status of link on the project_update page"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_active(
            self.superuser, 'sodar-pr-nav-project-update', self.sidebar_ids, url
        )


class TestProjectSearchResultsView(UITestBase):
    """Tests for ProjectSearchResultsView UI"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:search')

    def test_search_results(self):
        """Test project search items visibility according to user permissions"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_viewer_cat, 1),
            (self.user_finder_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_viewer, 1),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'test'})
        self.assert_element_count(expected, url, 'sodar-pr-project-search-item')

    def test_search_type_project(self):
        """Test project search items visibility with project type"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_viewer_cat, 1),
            (self.user_finder_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_viewer, 1),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'test type:project'})
        self.assert_element_count(expected, url, 'sodar-pr-project-search-item')

    def test_search_type_nonexisting(self):
        """Test project search items visibility with a nonexisting type"""
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'test type:Jaix1au'})
        self.assert_element_count(expected, url, 'sodar-pr-project-search-item')

    def test_search_project_link(self):
        """Test project link visibility according to user permissions"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_viewer_cat, 1),
            (self.user_finder_cat, 0),  # This should not exist
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_viewer, 1),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'test'})
        self.assert_element_count(
            expected, url, 'sodar-pr-project-search-link', attribute='class'
        )

    def test_search_project_findable_link(self):
        """Test project findable link visibility"""
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 1),  # Finder user should see this
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'test'})
        self.assert_element_count(
            expected, url, 'sodar-pr-project-findable', attribute='class'
        )


class TestProjectDetailView(RemoteSiteMixin, RemoteProjectMixin, UITestBase):
    """Tests for ProjectDetailView UI"""

    @classmethod
    def _get_pr_links(cls, *args) -> list[str]:
        """Return full IDs of project links"""
        return ['sodar-pr-link-project-' + x for x in args]

    def _get_pr_item_vis_count(self) -> int:
        return len(
            [
                e
                for e in self.selenium.find_elements(
                    By.CLASS_NAME, 'sodar-pr-project-list-item'
                )
                if e.get_attribute('style') != 'display: none;'
            ]
        )

    def _setup_remotes(
        self,
        site_mode: str = SITE_MODE_TARGET,
        level: str = REMOTE_LEVEL_READ_ROLES,
        user_visibility: bool = True,
    ):
        """Create remote site and project with given user_visibility setting"""
        self.remote_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=site_mode,
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=user_visibility,
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=level,
            project=self.project,
            date_access=timezone.now(),
        )

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
        self.wait_kw = {
            'wait_elem': 'sodar-pr-project-title',
            'wait_loc': 'CLASS_NAME',
        }
        self.cat_stat_wait_kw = {
            'wait_elem': 'sodar-pr-dashboard-card-stats',
            'wait_loc': 'CLASS_NAME',
        }

    def test_project_links(self):
        """Test visibility of project links"""
        expected = [
            (self.superuser, self._get_pr_links('roles', 'update', 'star')),
            (
                self.user_owner_cat,
                self._get_pr_links('roles', 'update', 'star'),
            ),
            (
                self.user_delegate_cat,
                self._get_pr_links('roles', 'update', 'star'),
            ),
            (self.user_contributor_cat, self._get_pr_links('roles', 'star')),
            (self.user_guest_cat, self._get_pr_links('roles', 'star')),
            (self.user_viewer_cat, self._get_pr_links('roles', 'star')),
            (self.user_owner, self._get_pr_links('roles', 'update', 'star')),
            (self.user_delegate, self._get_pr_links('roles', 'update', 'star')),
            (self.user_contributor, self._get_pr_links('roles', 'star')),
            (self.user_guest, self._get_pr_links('roles', 'star')),
            (self.user_viewer, self._get_pr_links('roles', 'star')),
        ]
        self.assert_element_set(expected, PROJECT_LINK_IDS, self.url)

    def test_project_links_category(self):
        """Test visibility of top level category links"""
        expected = [
            (
                self.superuser,
                self._get_pr_links('roles', 'update', 'create', 'star'),
            ),
            (
                self.user_owner_cat,
                self._get_pr_links('roles', 'update', 'create', 'star'),
            ),
            (
                self.user_delegate_cat,
                self._get_pr_links('roles', 'update', 'create', 'star'),
            ),
            (
                self.user_contributor_cat,
                self._get_pr_links('roles', 'create', 'star'),
            ),
            (self.user_guest_cat, self._get_pr_links('roles', 'star')),
            (self.user_viewer_cat, self._get_pr_links('roles', 'star')),
            (self.user_finder_cat, self._get_pr_links('roles', 'star')),
            (self.user_owner, self._get_pr_links('star')),
            (self.user_delegate, self._get_pr_links('star')),
            (self.user_contributor, self._get_pr_links('star')),
            (self.user_guest, self._get_pr_links('star')),
            (self.user_viewer, self._get_pr_links('roles', 'star')),
        ]
        self.assert_element_set(expected, PROJECT_LINK_IDS, self.url_cat)

    def test_project_links_read_only(self):
        """Test visibility of project links with site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        expected = [
            (self.superuser, self._get_pr_links('roles', 'update')),
            (self.user_owner_cat, self._get_pr_links('roles')),
            (self.user_delegate_cat, self._get_pr_links('roles')),
            (self.user_contributor_cat, self._get_pr_links('roles')),
            (self.user_guest_cat, self._get_pr_links('roles')),
            (self.user_viewer_cat, self._get_pr_links('roles')),
            (self.user_owner, self._get_pr_links('roles')),
            (self.user_delegate, self._get_pr_links('roles')),
            (self.user_contributor, self._get_pr_links('roles')),
            (self.user_guest, self._get_pr_links('roles')),
            (self.user_viewer, self._get_pr_links('roles')),
        ]
        self.assert_element_set(expected, PROJECT_LINK_IDS, self.url)

    def test_project_category_stats(self):
        """Test category stats visibility under project (should not exist)"""
        self.login_and_redirect(self.user_owner, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-details-card-stats')

    def test_copy_uuid_visibility_default(self):
        """Test default UUID copy button visibility (should not be visible)"""
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in users:
            self.login_and_redirect(user, self.url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(By.ID, 'sodar-pr-btn-copy-uuid')

    def test_copy_uuid_visibility_enabled(self):
        """Test UUID copy button visibility with setting enabled"""
        app_settings.set(
            plugin_name='userprofile',
            setting_name='enable_project_uuid_copy',
            value=True,
            user=self.user_owner,
        )
        self.assert_element_exists(
            [self.user_owner], self.url, 'sodar-pr-btn-copy-uuid', True
        )

    def test_plugin_links(self):
        """Test visibility of app plugin links"""
        expected = [(self.superuser, len(plugin_api.get_active_plugins()))]
        self.assert_element_count(
            expected, self.url, 'sodar-pr-link-app-plugin'
        )

    def test_plugin_cards(self):
        """Test visibility of app plugin cards"""
        expected = [(self.superuser, len(plugin_api.get_active_plugins()))]
        self.assert_element_count(expected, self.url, 'sodar-pr-app-item')

    def test_limited_alert(self):
        """Test visibility of limited access alert"""
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 1),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_viewer, 1),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-pr-details-alert-limited'
        )

    def test_limited_alert_category(self):
        """Test visibility of limited access alert for category"""
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 1),
            (self.user_finder_cat, 1),
        ]
        self.assert_element_count(
            expected, self.url_cat, 'sodar-pr-details-alert-limited'
        )

    def test_remote_project(self):
        """Test remote project visbility for all users"""
        self._setup_remotes()
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in users:
            self.login_and_redirect(user, self.url)
            elem = self.selenium.find_element(
                By.CLASS_NAME, 'sodar-pr-link-remote-target'
            )
            self.assertIn('btn-info', elem.get_attribute('class'))
            if user == self.superuser:  # No need to test these for all users
                self.assertEqual(elem.text, REMOTE_SITE_NAME)
                self.assertEqual(
                    elem.get_attribute('href'), self.remote_site.url + self.url
                )
                self.assertIsNone(elem.get_attribute('disabled'))

    def test_remote_project_user_visibility_disabled(self):
        """Test remote project visibility with user_visibility=False"""
        self._setup_remotes(user_visibility=False)
        users = [self.user_delegate, self.user_contributor, self.user_guest]
        for user in users:
            self.login_and_redirect(user, self.url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.ID, 'sodar-pr-details-card-remote'
                )
        # Greyed out for superuser and owner
        for user in [self.superuser, self.user_owner]:
            self.login_and_redirect(user, self.url)
            elem = self.selenium.find_element(
                By.CLASS_NAME, 'sodar-pr-link-remote-target'
            )
            self.assertIn('btn-secondary', elem.get_attribute('class'))

    def test_remote_project_revoked(self):
        """Test remote project with REVOKED level"""
        self._setup_remotes(level=REMOTE_LEVEL_REVOKED)
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in users:
            self.login_and_redirect(user, self.url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.ID, 'sodar-pr-details-card-remote'
                )

    def test_remote_project_not_accessed(self):
        """Test non-accessed remote project"""
        self._setup_remotes()
        self.remote_project.date_access = None
        self.remote_project.save()
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-pr-link-remote-target'
        )
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    def test_remote_project_update(self):
        """Test non-accessed remote project with client side update"""
        self._setup_remotes()
        self.remote_project.date_access = None
        self.remote_project.save()
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-pr-link-remote-target'
        )
        self.assertEqual(elem.get_attribute('disabled'), 'true')
        self.remote_project.date_access = timezone.now()
        self.remote_project.save()
        xp = (
            '//a[contains(@class, "sodar-pr-link-remote-target") '
            'and not(@disabled)]'
        )
        WebDriverWait(self.selenium, 15).until(
            ec.presence_of_element_located((By.XPATH, xp))
        )
        self.assertEqual(elem.get_attribute('disabled'), None)

    def test_peer_project_source(self):
        """Test visibility of peer projects on SOURCE site"""
        self._setup_remotes(site_mode=SITE_MODE_PEER)
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in users:
            self.login_and_redirect(user, self.url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.ID, 'sodar-pr-details-card-remote'
                )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_peer_project(self):
        """Test peer projects on TARGET site with user_display=True"""
        # There needs to be a source mode remote project as source project,
        # otherwise peer project logic wont be reached
        source_site = self.make_site(
            name='Second Remote Site',
            url='second_remote.site',
            mode=SITE_MODE_SOURCE,
            description='',
            secret=build_secret(),
            user_display=True,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=source_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
            date_access=timezone.now(),
        )
        self._setup_remotes(site_mode=SITE_MODE_PEER)

        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in users:
            self.login_and_redirect(user, self.url)
            elems = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(elems), 2)
            self.assertIn(
                'sodar-pr-link-remote-source', elems[0].get_attribute('class')
            )
            self.assertIn(
                'sodar-pr-link-remote-peer', elems[1].get_attribute('class')
            )
            if user == self.superuser:
                self.assertEqual(
                    elems[1].get_attribute('href'),
                    self.remote_site.url + self.url,
                )
                self.assertIsNone(elems[1].get_attribute('disabled'))

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_peer_project_user_visibility_disabled(self):
        """Test peer projects on TARGET site with user_display=False"""
        source_site = self.make_site(
            name='Second Remote Site',
            url='second_remote.site',
            mode=SITE_MODE_SOURCE,
            description='',
            secret=build_secret(),
            user_display=False,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=source_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self._setup_remotes(site_mode=SITE_MODE_PEER, user_visibility=False)

        expected_true = [self.superuser, self.user_owner_cat, self.user_owner]
        expected_false = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in expected_true:
            self.login_and_redirect(user, self.url)
            elems = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(elems), 2)
            self.assertIn(
                'sodar-pr-link-remote-source', elems[0].get_attribute('class')
            )
            self.assertIn(
                'sodar-pr-link-remote-peer', elems[1].get_attribute('class')
            )
        for user in expected_false:
            self.login_and_redirect(user, self.url)
            elems = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(elems), 1)
            self.assertIn(
                'sodar-pr-link-remote-source', elems[0].get_attribute('class')
            )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_peer_project_revoked(self):
        """Test peer project with REVOKED level"""
        source_site = self.make_site(
            name='Second Remote Site',
            url='second_remote.site',
            mode=SITE_MODE_SOURCE,
            description='',
            secret=build_secret(),
            user_display=False,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=source_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self._setup_remotes(
            site_mode=SITE_MODE_PEER, level=REMOTE_LEVEL_REVOKED
        )
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        for user in users:
            self.login_and_redirect(user, self.url)
            elems = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(elems), 1)
            self.assertIn(
                'sodar-pr-link-remote-source', elems[0].get_attribute('class')
            )

    def test_public_access_default(self):
        """Test public access icon with non-public project"""
        self.login_and_redirect(self.user_owner, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-public')

    def test_public_access_guest_as_owner(self):
        """Test public guest access project as owner"""
        self.project.set_public_access(self.role_guest)
        self.login_and_redirect(self.user_owner, self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-public')
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')

    def test_public_access_viewer_as_owner(self):
        """Test public viewer access project as owner"""
        self.project.set_public_access(self.role_viewer)
        self.login_and_redirect(self.user_owner, self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-public')
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')

    def test_public_access_guest_no_role(self):
        """Test public guest access project without role"""
        self.project.set_public_access(self.role_guest)
        self.login_and_redirect(self.user_no_roles, self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-public')
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')

    def test_public_access_viewer_no_role(self):
        """Test public viewer access project without role"""
        self.project.set_public_access(self.role_viewer)
        self.login_and_redirect(self.user_no_roles, self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-public')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')
        )

    def test_archive_default(self):
        """Test archive icon and alert visibility (should not be visible)"""
        self.login_and_redirect(self.user_owner, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-archive')
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-alert-archive')

    def test_archive_archived(self):
        """Test archive icon and alert visibility for archived project"""
        self.project.set_archive()
        self.login_and_redirect(self.user_owner, self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-alert-archive')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-header-icon-archive')
        )

    def test_category_stats(self):
        """Test rendering of category statistics"""
        self.login_and_redirect(
            self.user_owner, self.url_cat, **self.cat_stat_wait_kw
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-card-stats')
        )
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-dashboard-card-stats'
        )
        self.assertEqual(len(elems), 3)

    def test_category_project_list(self):
        """Test rendering of project list in category"""
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_highlight', user=self.user_owner
            ),
            True,
        )
        self.login_and_redirect(self.user_owner, self.url_cat, **self.wait_kw)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-pr-project-link'
        )
        self.assertEqual(
            elem.get_attribute('innerHTML'),
            f'<strong>{self.project.title}</strong>',
        )

    def test_category_project_list_no_highlight(self):
        """Test rendering of project list in category with no highlight"""
        app_settings.set(
            APP_NAME, 'project_list_highlight', False, user=self.user_owner
        )
        self.login_and_redirect(self.user_owner, self.url_cat, **self.wait_kw)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-pr-project-link'
        )
        self.assertEqual(elem.get_attribute('innerHTML'), self.project.title)

    def test_category_project_list_subcategory(self):
        """Test rendering of project list in category with subcategory"""
        sub_cat_title = 'SubCategory'
        sub_cat = self.make_project(
            sub_cat_title, PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(sub_cat, self.user_owner, self.role_owner)
        # Move project under subcategory
        self.project.parent = sub_cat
        self.project.save()
        self.login_and_redirect(self.user_owner, self.url_cat, **self.wait_kw)
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-project-link'
        )
        self.assertEqual(
            elems[0].get_attribute('innerHTML'),
            f'{sub_cat.title}',
        )
        self.assertEqual(
            elems[1].get_attribute('innerHTML'),
            f'{sub_cat.title}{CAT_DELIMITER}<strong>{self.project.title}'
            f'</strong>',
        )

    def test_category_project_list_star(self):
        """Test category project list star filter"""
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user_owner
            ),
            False,
        )
        # Set up new starred project
        new_project = self.make_project(
            'NewProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.make_assignment(new_project, self.user_owner, self.role_owner)
        app_settings.set(
            APP_NAME,
            'project_star',
            True,
            project=new_project,
            user=self.user_owner,
        )
        self.login_and_redirect(self.user_owner, self.url_cat, **self.wait_kw)
        self.assertEqual(self._get_pr_item_vis_count(), 2)
        button = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-link-star'
        )
        button.click()
        self.assertEqual(self._get_pr_item_vis_count(), 1)
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_list_home_starred', user=self.user_owner
            ),
            False,
        )  # Not in HomeView, default value should not be set

    def test_category_public_stats_no_role(self):
        """Test category with category_public_stats and user with no role"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        self.login_and_redirect(
            self.user_no_roles, self.url_cat, **self.cat_stat_wait_kw
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-card-readme')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-card-stats')
        )
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-dashboard-card-stats'
        )
        self.assertEqual(len(elems), 3)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-project-list-table')

    def test_category_public_stats_local_role(self):
        """Test category with category_public_stats and user with local role"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        self.login_and_redirect(self.user_contributor_cat, self.url_cat)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-card-readme')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-project-list-table')
        )

    def test_category_public_stats_child_role(self):
        """Test category with category_public_stats and user with child role"""
        app_settings.set(
            APP_NAME, 'category_public_stats', True, project=self.category
        )
        self.login_and_redirect(self.user_contributor, self.url_cat)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-details-alert-limited')
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-details-card-readme')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-project-list-table')
        )


class TestProjectCreateView(RemoteSiteMixin, UITestBase):
    """Tests for ProjectCreateView UI"""

    def setUp(self):
        super().setUp()
        self.remote_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=True,
            sodar_uuid=REMOTE_SITE_UUID,
        )
        self.url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.url_top = reverse('projectroles:create')

    def test_owner_widget_top(self):
        """Test rendering the owner widget on the top level"""
        self.assert_element_exists(
            [self.superuser], self.url_top, 'div_id_owner', True
        )

    def test_owner_widget_sub(self):
        """Test rendering the owner widget under a category"""
        # Add new user, make them a contributor in category
        new_user = self.make_user('new_user')
        self.make_assignment(self.category, new_user, self.role_contributor)
        self.assert_element_exists(
            [self.superuser], self.url, 'div_id_owner', True
        )
        self.assert_element_exists(
            [self.user_owner, new_user], self.url, 'div_id_owner', False
        )

    def test_archive_button(self):
        """Test rendering form without archive button"""
        self.assert_element_exists(
            [self.superuser], self.url_top, 'sodar-pr-btn-archive', False
        )

    def test_delete_button(self):
        """Test rendering form without delete button"""
        self.assert_element_exists(
            [self.superuser], self.url_top, 'sodar-pr-btn-delete', False
        )

    def test_fields_top(self):
        """Test rendering of dynamic fields for top level creation view"""
        self.login_and_redirect(self.superuser, self.url_top)
        self.assert_displayed(By.ID, PUBLIC_ACCESS_ID, False)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, REMOTE_SITE_ID)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, False)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, True)

    def test_fields_project(self):
        """Test rendering of dynamic fields for project creation"""
        self.login_and_redirect(self.superuser, self.url)
        self.assert_displayed(By.ID, PUBLIC_ACCESS_ID, False)
        self.assert_displayed(By.ID, REMOTE_SITE_ID, False)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, False)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, False)
        select = Select(
            self.selenium.find_element(By.CSS_SELECTOR, PROJECT_SELECT_CSS)
        )
        select.select_by_value(PROJECT_TYPE_PROJECT)
        self.assertEqual(select.first_selected_option.text, 'Project')
        WebDriverWait(self.selenium, 10).until(
            ec.visibility_of_element_located((By.ID, PUBLIC_ACCESS_ID))
        )
        self.assert_displayed(By.ID, REMOTE_SITE_ID, True)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, True)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, False)

    def test_fields_category(self):
        """Test rendering of dynamic fields for category creation"""
        self.login_and_redirect(self.superuser, self.url)
        self.assert_displayed(By.ID, PUBLIC_ACCESS_ID, False)
        self.assert_displayed(By.ID, REMOTE_SITE_ID, False)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, False)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, False)
        select = Select(
            self.selenium.find_element(By.CSS_SELECTOR, PROJECT_SELECT_CSS)
        )
        select.select_by_value(PROJECT_TYPE_CATEGORY)
        self.assertEqual(select.first_selected_option.text, 'Category')
        WebDriverWait(self.selenium, 10).until(
            ec.visibility_of_element_located((By.ID, CATEGORY_SETTING_ID))
        )
        self.assert_displayed(By.ID, PUBLIC_ACCESS_ID, False)
        self.assert_displayed(By.ID, REMOTE_SITE_ID, False)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, False)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, True)

    def test_settings_label_icon(self):
        """Test rendering of app settings icon for project creation"""
        self.login_and_redirect(self.superuser, self.url)
        select = Select(
            self.selenium.find_element(By.CSS_SELECTOR, PROJECT_SELECT_CSS)
        )
        select.select_by_value(PROJECT_TYPE_PROJECT)
        WebDriverWait(self.selenium, 10).until(
            ec.presence_of_element_located((By.TAG_NAME, 'svg'))
        )
        find_args = (By.CSS_SELECTOR, f'div[id="{PROJECT_SETTING_ID}"]')
        logo = self.selenium.find_element(*find_args).find_element(
            By.TAG_NAME, 'svg'
        )
        self.assertTrue(logo.is_displayed())

    def test_submit_button(self):
        """Test rendering of submit button"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-btn-submit-once'
        )
        self.assertEqual(elem.text, 'Create')
        self.assertTrue(elem.is_enabled())


class TestProjectUpdateView(RemoteSiteMixin, RemoteProjectMixin, UITestBase):
    """Tests for ProjectUpdateView UI"""

    def setUp(self):
        super().setUp()
        self.remote_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=True,
            sodar_uuid=REMOTE_SITE_UUID,
        )
        self.url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )

    def test_archive_button(self):
        """Test rendering archive button"""
        self.assert_element_exists(
            [self.superuser], self.url, 'sodar-pr-btn-archive', True
        )
        element = self.selenium.find_element(By.ID, 'sodar-pr-btn-archive')
        self.assertEqual(element.text, 'Archive')

    def test_archive_button_archived(self):
        """Test rendering archive button with archived project"""
        self.project.set_archive()
        self.assert_element_exists(
            [self.superuser], self.url, 'sodar-pr-btn-archive', True
        )
        element = self.selenium.find_element(By.ID, 'sodar-pr-btn-archive')
        self.assertEqual(element.text, 'Unarchive')

    def test_delete_button(self):
        """Test rendering delete button"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_delete_button_category_with_children(self):
        """Test rendering delete button with category and children"""
        self.login_and_redirect(self.superuser, self.url_cat)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    def test_delete_button_category_no_children(self):
        """Test rendering delete button with category and no children"""
        self.project.delete()
        self.login_and_redirect(self.superuser, self.url_cat)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_delete_button_remote(self):
        """Test rendering delete button with non-revoked remote project"""
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    def test_delete_button_remote_revoked(self):
        """Test rendering delete button with revoked remote project"""
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_REVOKED,
            project=self.project,
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertIsNone(elem.get_attribute('disabled'))

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_delete_button_remote_target(self):
        """Test rendering delete button with non-revoked remote project as target site"""
        self.remote_site.mode = SITE_MODE_SOURCE
        self.remote_site.save()
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_delete_button_remote_revoked_target(self):
        """Test rendering delete button with non-revoked remote project as target site"""
        self.remote_site.mode = SITE_MODE_SOURCE
        self.remote_site.save()
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_REVOKED,
            project=self.project,
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-delete')
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_fields_project(self):
        """Test field visibility for project update"""
        self.login_and_redirect(self.superuser, self.url)
        self.assert_displayed(By.ID, PUBLIC_ACCESS_ID, True)
        self.assert_displayed(By.ID, REMOTE_SITE_ID, True)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, True)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, False)

    def test_fields_category(self):
        """Test field visibility for category update"""
        self.login_and_redirect(self.superuser, self.url_cat)
        self.assert_displayed(By.ID, PUBLIC_ACCESS_ID, False)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, REMOTE_SITE_ID)
        self.assert_displayed(By.ID, PROJECT_SETTING_ID, False)
        self.assert_displayed(By.ID, CATEGORY_SETTING_ID, True)

    def test_remote_field_enable(self):
        """Test enabling remote site field"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, REMOTE_SITE_ID)
        self.assertEqual(elem.is_selected(), False)
        elem.click()
        with self.assertRaises(TimeoutException):
            WebDriverWait(self.selenium, 3).until(ec.alert_is_present())
        self.assertEqual(elem.is_selected(), True)
        elem.click()  # Disable again
        with self.assertRaises(TimeoutException):
            WebDriverWait(self.selenium, 3).until(ec.alert_is_present())
        self.assertEqual(elem.is_selected(), False)

    def test_remote_field_disable(self):
        """Test disabling previously enabled remote site field"""
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, REMOTE_SITE_ID)
        self.assertEqual(elem.is_selected(), True)
        elem.click()
        WebDriverWait(self.selenium, 3).until(ec.alert_is_present())
        self.selenium.switch_to.alert.accept()
        self.assertEqual(elem.is_selected(), False)

    def test_remote_field_disable_cancel(self):
        """Test canceling the disabling of previously enabled remote site field"""
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self.selenium.find_element(By.ID, REMOTE_SITE_ID)
        self.assertEqual(elem.is_selected(), True)
        elem.click()
        WebDriverWait(self.selenium, 3).until(ec.alert_is_present())
        self.selenium.switch_to.alert.dismiss()
        self.assertEqual(elem.is_selected(), True)


class TestProjectArchiveView(UITestBase):
    """Tests for ProjectArchiveView UI"""

    def test_archive_button(self):
        """Test rendering of archive button"""
        url = reverse(
            'projectroles:archive', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-btn-confirm-archive', True
        )

    def test_archive_button_archived(self):
        """Test rendering of archive button with archived project"""
        self.project.set_archive()
        url = reverse(
            'projectroles:archive', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-btn-confirm-unarchive', True
        )


class TestProjectDeleteView(UITestBase):
    """Tests for ProjectDeleteView UI"""

    def test_render(self):
        """Test rendering of project delete confirmation form"""
        url = reverse(
            'projectroles:delete', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(self.superuser, url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-pr-btn-confirm-delete')
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.NAME, 'delete_host_confirm')
        )


class TestProjectRoleView(RemoteTargetMixin, UITestBase):
    """Tests for ProjectRoleView UI"""

    def _get_role_dropdown(
        self, user: SODARUser, owner: bool = False
    ) -> WebElement:
        """Return role dropdown for a role"""
        row = self.selenium.find_element(
            By.XPATH,
            f'//tr[contains(@class, "sodar-pr-role-list-row") and '
            f'@data-user-uuid="{user.sodar_uuid}"]',
        )
        class_name = 'sodar-pr-role-dropdown'
        if owner:
            class_name += '-owner'
        return row.find_element(By.CLASS_NAME, class_name)

    def _get_role_items(self, user: SODARUser) -> list[WebElement]:
        """Return role dropdown items for a role"""
        dropdown = self._get_role_dropdown(user)
        return dropdown.find_elements(By.CLASS_NAME, 'dropdown-item')

    def setUp(self):
        super().setUp()
        self.user_assign = self.make_user('user_assign')
        self.url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        self.wait_kw = {
            'wait_elem': 'dataTable',
            'wait_loc': 'CLASS_NAME',
        }

    def test_render_role_row(self):
        """Test rendering user role row"""
        self.login_and_redirect(self.user_owner, self.url)
        row = self.selenium.find_element(
            By.XPATH,
            f'//tr[@data-user-uuid="{self.user_contributor.sodar_uuid}"]',
        )
        for td in row.find_elements(By.TAG_NAME, 'td')[:3]:
            self.assertNotIn('text-secondary', td.get_attribute('class'))

    def test_render_role_row_inactive(self):
        """Test rendering user role row with inactive user"""
        self.user_contributor.is_active = False
        self.user_contributor.save()
        self.login_and_redirect(self.user_owner, self.url)
        row = self.selenium.find_element(
            By.XPATH,
            f'//tr[@data-user-uuid="{self.user_contributor.sodar_uuid}"]',
        )
        for td in row.find_elements(By.TAG_NAME, 'td')[:3]:
            self.assertIn('text-secondary', td.get_attribute('class'))

    def test_leave_button_owner(self):
        """Test rendering leave project button as owner"""
        self.login_and_redirect(self.user_owner, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    def test_leave_button_owner_read_only(self):
        """Test rendering leave project button as owner with site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        self.login_and_redirect(self.user_owner, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')

    def test_leave_button_contributor(self):
        """Test rendering leave project button as contributor"""
        self.login_and_redirect(self.user_contributor, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')
        self.assertIsNone(elem.get_attribute('disabled'))

    def test_leave_button_contributor_read_only(self):
        """Test rendering leave project button as contributor with site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        self.login_and_redirect(self.user_contributor, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')

    def test_leave_button_inherit(self):
        """Test rendering leave project button as inherited contributor"""
        self.login_and_redirect(self.user_contributor_cat, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_leave_button_target(self):
        """Test rendering leave project button as target"""
        self.set_up_as_target(projects=[self.category, self.project])
        self.login_and_redirect(self.user_contributor, self.url)
        elem = self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')
        self.assertEqual(elem.get_attribute('disabled'), 'true')

    def test_leave_button_superuser_no_role(self):
        """Test rendering leave project button as superuser with no role"""
        self.login_and_redirect(self.superuser, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')

    def test_leave_button_public_access_no_role(self):
        """Test rendering leave button in public access project with no role"""
        self.project.set_public_access(self.role_guest)
        self.login_and_redirect(self.user_no_roles, self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-pr-btn-leave-project')

    def test_role_ops(self):
        """Test rendering role operations dropdown"""
        good_users = [self.superuser, self.user_owner, self.user_delegate]
        bad_users = [self.user_contributor, self.user_guest]
        self.assert_element_exists(
            good_users, self.url, 'sodar-pr-role-ops-dropdown', True
        )
        self.assert_element_exists(
            bad_users, self.url, 'sodar-pr-role-ops-dropdown', False
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_role_ops_target(self):
        """Test rendering role operations dropdown as target"""
        self.set_up_as_target(projects=[self.category, self.project])
        non_superusers = [
            self.user_owner,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        self.login_and_redirect(self.superuser, self.url)
        btn = self.selenium.find_element(By.ID, 'sodar-pr-role-ops-btn')
        self.assertEqual(btn.is_enabled(), False)
        self.assert_element_exists(
            non_superusers, self.url, 'sodar-pr-role-ops-dropdown', False
        )

    def test_role_ops_read_only(self):
        """Test rendering role operations dropdown with site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        good_users = [self.superuser]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        self.assert_element_exists(
            good_users, self.url, 'sodar-pr-role-ops-dropdown', True
        )
        self.assert_element_exists(
            bad_users, self.url, 'sodar-pr-role-ops-dropdown', False
        )

    def test_role_ops_invite(self):
        """Test visibility of role operations invite item"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        expected_false = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        self.assert_element_exists(
            expected_true, self.url, 'sodar-pr-role-ops-invite', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-pr-role-ops-invite', False
        )

    def test_role_ops_create(self):
        """Test visibility of role operations create item"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        expected_false = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
        ]
        self.assert_element_exists(
            expected_true, self.url, 'sodar-pr-role-ops-create', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-pr-role-ops-create', False
        )

    def test_role_dropdown(self):
        """Test visibility of role management dropdown"""
        expected = [
            (self.superuser, 8),
            (self.user_owner_cat, 8),
            (self.user_delegate_cat, 6),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 8),
            (self.user_delegate, 6),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_viewer, 0),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-pr-role-dropdown', attribute='class'
        )

    def test_role_dropdown_owner_local(self):
        """Test role dropdown items for local owner"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elem = self._get_role_dropdown(self.user_owner, owner=True)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-transfer')
        )

    def test_role_dropdown_owner_inherited(self):
        """Test role dropdown items for inherited owner"""
        # Set category owner to new user
        self.owner_as_cat.user = self.user_assign
        self.owner_as_cat.save()
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        with self.assertRaises(NoSuchElementException):
            self._get_role_dropdown(self.user_assign, owner=True)

    def test_role_dropdown_delegate_local(self):
        """Test role dropdown items for local delegate"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elem = self._get_role_dropdown(self.user_delegate)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-update')
        )
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-delete')
        )

    def test_role_dropdown_delegate_inherited(self):
        """Test role dropdown items for inherited delegate"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        with self.assertRaises(NoSuchElementException):
            self._get_role_dropdown(self.user_delegate_cat)

    def test_role_dropdown_contrib_local(self):
        """Test role dropdown items for local contributor"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elem = self._get_role_dropdown(self.user_contributor)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-update')
        )
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-delete')
        )

    def test_role_dropdown_contrib_inherited(self):
        """Test role dropdown items for inherited contributor"""
        self.make_assignment(
            self.category, self.user_assign, self.role_contributor
        )
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elem = self._get_role_dropdown(self.user_assign)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-promote')
        )
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-update')
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-delete')

    def test_role_dropdown_guest_local(self):
        """Test role dropdown items for local guest"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elem = self._get_role_dropdown(self.user_guest)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-update')
        )
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-delete')
        )

    def test_role_dropdown_guest_inherited(self):
        """Test role dropdown items for inherited guest"""
        self.make_assignment(self.category, self.user_assign, self.role_guest)
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elem = self._get_role_dropdown(self.user_assign)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-promote')
        )
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-update')
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-item-delete')

    def test_role_dropdown_read_only(self):
        """Test role dropdown with site read-only mode"""
        app_settings.set(APP_NAME, 'site_read_only', True)
        expected = [
            (self.superuser, 8),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_viewer, 0),
        ]
        self.assert_element_count(
            expected,
            self.url,
            'sodar-pr-role-dropdown',
            attribute='class',
            **self.wait_kw,
        )

    def test_pagination_default(self):
        """Test role list pagination with default settings"""
        self.assertEqual(settings.PROJECTROLES_ROLE_PAGINATION, 15)
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-role-list-row'
        )
        self.assertEqual(len(elems), 10)
        elem = self.selenium.find_element(By.CLASS_NAME, 'dataTables_paginate')
        self.assertEqual(elem.is_displayed(), False)

    @override_settings(PROJECTROLES_ROLE_PAGINATION=2)
    def test_pagination_limit(self):
        """Test role list pagination with limit"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-role-list-row'
        )
        self.assertEqual(len(elems), 2)
        elem = self.selenium.find_element(By.CLASS_NAME, 'dataTables_paginate')
        self.assertEqual(elem.is_displayed(), True)

    def test_filter(self):
        """Test role list filtering"""
        self.login_and_redirect(self.superuser, self.url, **self.wait_kw)
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-role-list-row'
        )
        self.assertEqual(len(elems), 10)
        f_input = self.selenium.find_element(By.ID, 'sodar-pr-role-list-filter')
        f_input.send_keys('owner')
        elems = self.selenium.find_elements(
            By.CLASS_NAME, 'sodar-pr-role-list-row'
        )
        self.assertEqual(len(elems), 2)  # Category and project owner


class TestRoleAssignmentCreateView(UITestBase):
    """Tests for RoleAssignmentCreateView UI"""

    def test_role_preview(self):
        """Test visibility of role preview popup"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.login_and_redirect(self.user_owner, url)

        button = self.selenium.find_element(
            By.ID, 'sodar-pr-email-preview-link'
        )
        button.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, 'sodar-email-body'))
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-email-body')
        )

    def test_widget_user_options(self):
        """Test visibility of user options given by the autocomplete widget"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.login_and_redirect(self.user_owner, url)

        widget = self.selenium.find_element(
            By.CLASS_NAME, 'select2-container--default'
        )
        widget.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, 'select2-id_user-results'))
        )

        # Assert that options are displayed
        self.assertIsNotNone(
            self.selenium.find_element(By.CLASS_NAME, 'select2-results__option')
        )
        self.assertEqual(
            len(
                self.selenium.find_elements(
                    By.CLASS_NAME, 'select2-selection__rendered'
                )
            ),
            1,
        )


class TestRoleAssignmentDeleteView(UITestBase):
    """Tests for RoleAssignmentDeleteView UI"""

    def test_render(self):
        """Test rendering RoleAssignment deletion confirm view"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.login_and_redirect(self.superuser, url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-inherit'
            )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-child'
            )

    def test_render_inherit(self):
        """Test rendering with inherited role remaining for user"""
        self.make_assignment(
            self.category, self.user_contributor, self.role_contributor
        )
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.login_and_redirect(self.superuser, url)
        self.assertIsNotNone(
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-inherit'
            )
        )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-child'
            )

    def test_render_children(self):
        """Test rendering with inherited child roles to be removed"""
        user_new = self.make_user('user_new')
        new_as = self.make_assignment(
            self.category, user_new, self.role_contributor
        )
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': new_as.sodar_uuid},
        )
        self.login_and_redirect(self.superuser, url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-inherit'
            )
        self.assertIsNotNone(
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-child'
            )
        )

    def test_render_children_inherit(self):
        """Test rendering as finder with inherited child roles"""
        user_new = self.make_user('user_new')
        new_as = self.make_assignment(self.category, user_new, self.role_finder)
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': new_as.sodar_uuid},
        )
        self.login_and_redirect(self.superuser, url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-inherit'
            )
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(
                By.ID, 'sodar-pr-role-delete-alert-child'
            )


class TestProjectInviteView(ProjectInviteMixin, UITestBase):
    """Tests for ProjectInviteView UI"""

    def test_invite_ops(self):
        """Test visibility of invite operations dropdown"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-role-ops-dropdown', True
        )

    def test_invite_ops_invite(self):
        """Test visibility of invite operations invite item"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-role-ops-invite', True
        )

    def test_invite_ops_create(self):
        """Test visibility of invite operations create item"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-pr-role-ops-create', True
        )

    def test_invite_dropdown(self):
        """Test visibility of invite dropdowns"""
        self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
        ]
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(
            expected, url, 'sodar-pr-invite-dropdown', attribute='class'
        )


class TestProjectInviteCreateView(UITestBase):
    """Tests for ProjectInviteCreateView UI"""

    def test_invite_preview(self):
        """Test visibility of invite preview popup"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.login_and_redirect(self.user_owner, url)

        button = self.selenium.find_element(
            By.ID, 'sodar-pr-invite-preview-link'
        )
        button.click()
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located((By.ID, 'sodar-email-body'))
        )
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-email-body')
        )


class TestProjectInviteProcessLocalView(ProjectInviteMixin, UITestBase):
    """Tests for ProjectInviteProcessLocalView UI"""

    def setUp(self):
        super().setUp()
        self.invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        self.url = self.build_selenium_url(
            reverse(
                'projectroles:invite_process_new_user',
                kwargs={'secret': self.invite.secret},
            )
        )

    def test_get(self):
        """Test ProjectInviteProcessLocalView GET"""
        # NOTE: No login
        self.selenium.get(self.url)
        with self.assertRaises(NoSuchElementException):
            self.selenium.find_element(By.ID, 'sodar-login-oidc-link')
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-btn-submit-once'
        )
        self.assertEqual(elem.text, 'Create')

    @override_settings(ENABLE_OIDC=True)
    def test_get_oidc(self):
        """Test GET with OIDC authentication enabled"""
        self.selenium.get(self.url)
        self.assertIsNotNone(
            self.selenium.find_element(By.ID, 'sodar-login-oidc-link')
        )
        elem = self.selenium.find_element(
            By.CLASS_NAME, 'sodar-btn-submit-once'
        )
        self.assertEqual(elem.text, 'Create')


class TestRemoteSiteListView(RemoteSiteMixin, UITestBase):
    """Tests for RemoteSiteListView UI"""

    def test_source_user_display(self):
        """Test site list user display elements on source site"""
        self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=True,
        )
        url = reverse('projectroles:remote_sites')
        self.login_and_redirect(self.superuser, url)

        # Check Visible to User column visibility
        remote_site_table = self.selenium.find_element(
            By.ID, 'sodar-pr-remote-site-table'
        )
        try:
            remote_site_table.find_element(
                By.XPATH, '//th[contains(text(), "Visible")]'
            )
        except NoSuchElementException:
            self.fail(
                'User Display column (header) should exist on SOURCE remote '
                'site overview'
            )
        try:
            remote_site_table.find_element(
                By.XPATH, '//td[contains(text(), "Yes")]'
            )
        except NoSuchElementException:
            self.fail(
                'User Display column (data) should exist on SOURCE remote site '
                'overview'
            )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_target_list_user_display(self):
        """Test site list user display elements on target site"""
        self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description='',
            secret=REMOTE_SITE_SECRET,
            user_display=True,
        )
        url = reverse('projectroles:remote_sites')
        self.login_and_redirect(self.superuser, url)

        # Check Visible to User column visibility
        remote_site_table = self.selenium.find_element(
            By.ID, 'sodar-pr-remote-site-table'
        )
        with self.assertRaises(NoSuchElementException):
            remote_site_table.find_element(
                By.XPATH, '//th[contains(text(), "Visible to users")]'
            )
        with self.assertRaises(NoSuchElementException):
            remote_site_table.find_element(
                By.XPATH, '//td[contains(text(), "Yes")]'
            )


class TestRemoteSiteCreateView(RemoteSiteMixin, UITestBase):
    """Tests for RemoteSiteCreateView UI"""

    def test_source_user_toggle(self):
        """Test site create form user display toggle on source site"""
        url = reverse('projectroles:remote_site_create')
        self.login_and_redirect(self.superuser, url)
        element = self.selenium.find_element(By.ID, 'div_id_user_display')
        self.assertIsNotNone(element)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_target_user_toggle(self):
        """Test site create form user display toggle on target site"""
        url = reverse('projectroles:remote_site_create')
        self.login_and_redirect(self.superuser, url)
        self.assert_displayed(By.ID, 'id_user_display', False)
