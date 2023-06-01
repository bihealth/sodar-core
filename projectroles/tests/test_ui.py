"""UI tests for the projectroles app"""

import socket
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import (
    SESSION_KEY,
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
)
from django.contrib.sessions.backends.db import SessionStore
from django.test import LiveServerTestCase, override_settings
from django.urls import reverse

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait, Select

from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins
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

# Local constants
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


class LiveUserMixin:
    """Mixin for creating users to work with LiveServerTestCase"""

    @classmethod
    def make_user(cls, user_name, superuser=False):
        """Make user, superuser if superuser=True"""
        kwargs = {
            'username': user_name,
            'password': 'password',
            'email': '{}@example.com'.format(user_name),
            'is_active': True,
        }
        if superuser:
            user = User.objects.create_superuser(**kwargs)
        else:
            user = User.objects.create_user(**kwargs)
        user.save()
        return user


class TestUIBase(
    LiveUserMixin,
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    LiveServerTestCase,
):
    """Base class for UI tests"""

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

    def setUp(self):
        socket.setdefaulttimeout(60)  # To get around Selenium hangups
        # Init Chrome
        options = webdriver.ChromeOptions()
        for arg in self.chrome_options:
            options.add_argument(arg)
        self.selenium = webdriver.Chrome(chrome_options=options)
        # Prevent ElementNotVisibleException
        self.selenium.set_window_size(self.window_size[0], self.window_size[1])

        # Init roles
        self.init_roles()
        # Init users
        self.superuser = self.make_user('admin', True)
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_delegate_cat = self.make_user('user_delegate_cat')
        self.user_contributor_cat = self.make_user('user_contributor_cat')
        self.user_guest_cat = self.make_user('user_guest_cat')
        self.user_finder_cat = self.make_user('user_finder_cat')
        self.user_owner = self.make_user('user_owner')
        self.user_delegate = self.make_user('user_delegate')
        self.user_contributor = self.make_user('user_contributor')
        self.user_guest = self.make_user('user_guest')
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

    def tearDown(self):
        # Shut down Selenium
        self.selenium.quit()
        super().tearDown()

    def build_selenium_url(self, url=''):
        """Build absolute URL to work with Selenium"""
        # NOTE: Chrome v77 refuses to accept cookies for "localhost" (see #337)
        return '{}{}'.format(
            self.live_server_url.replace('localhost', '127.0.0.1'), url
        )

    def login_and_redirect(
        self, user, url, wait_elem=None, wait_loc=DEFAULT_WAIT_LOC
    ):
        """
        Login with Selenium by setting a cookie, wait for redirect to given URL.

        If PROJECTROLES_TEST_UI_LEGACY_LOGIN=True, use legacy UI login method.

        :param user: User object
        :param url: URL to redirect to (string)
        """
        # Legacy login mode
        if getattr(settings, 'PROJECTROLES_TEST_UI_LEGACY_LOGIN', False):
            return self.login_and_redirect_with_ui(
                user, url, wait_elem, wait_loc
            )
        # Cookie login mode
        self.selenium.get(self.build_selenium_url('/blank/'))

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
        self, user, url, wait_elem=None, wait_loc=DEFAULT_WAIT_LOC
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
        users,
        url,
        element_id,
        exists,
        wait_elem=None,
        wait_loc=DEFAULT_WAIT_LOC,
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
        expected,
        url,
        search_string,
        attribute='id',
        path='//',
        exact=False,
        wait_elem=None,
        wait_loc=DEFAULT_WAIT_LOC,
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
                    'expected_user={}'.format(expected_user),
                )
            else:
                with self.assertRaises(NoSuchElementException):
                    self.selenium.find_element(
                        By.XPATH,
                        xpath.format(path, attribute, search_string),
                    )

    def assert_element_set(
        self,
        expected,
        all_elements,
        url,
        wait_elem=None,
        wait_loc=DEFAULT_WAIT_LOC,
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
        user,
        element_id,
        all_elements,
        url,
        wait_elem=None,
        wait_loc=DEFAULT_WAIT_LOC,
    ):
        """
        Assert the "active" status of an element based on logged user as well
        as unset status of other elements.

        :param user: User for logging in
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


class TestBaseTemplate(TestUIBase):
    """Tests for the base project template"""

    def test_admin_link(self):
        """Test admin site link visibility according to user permissions"""
        expected_true = [self.superuser]
        expected_false = [
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        url = reverse('home')
        elem_id = 'sodar-navbar-link-admin'
        self.assert_element_exists(expected_true, url, elem_id, True)
        self.assert_element_exists(expected_false, url, elem_id, False)


class TestHomeView(TestUIBase):
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

    def _get_item_vis_count(self):
        return len(
            [
                e
                for e in self.selenium.find_elements(
                    By.CLASS_NAME, 'sodar-pr-project-list-item'
                )
                if e.get_attribute('style') != 'display: none;'
            ]
        )

    def _get_list_item(self, project):
        return self.selenium.find_element(
            By.XPATH,
            '//tr[@class="sodar-pr-project-list-item '
            'sodar-pr-project-list-item-{}" and @data-uuid="{}"]'.format(
                project.type.lower(), project.sodar_uuid
            ),
        )

    def test_project_list_items(self):
        """Test visibility of project list items"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_finder_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
        ]
        elem_id = 'sodar-pr-project-list-item'
        self.assert_element_count(
            expected, self.url, elem_id, **self.wait_kwargs
        )
        self.assert_element_count(
            [(self.user_no_roles, 0)],
            self.url,
            elem_id,
            **self.wait_kwargs_empty
        )

    def test_project_list_items_public(self):
        """Test visibility of project list items with public access project"""
        self.project.set_public()
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_finder_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_no_roles, 2),
        ]
        self.assert_element_count(
            expected, self.url, 'sodar-pr-project-list-item', **self.wait_kwargs
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_list_items_anon(self):
        """Test visibility of project list items with anonymous access"""
        self.project.set_public()
        self.selenium.get(self.build_selenium_url(self.url))
        WebDriverWait(self.selenium, self.wait_time).until(
            ec.presence_of_element_located(
                (getattr(By, 'CLASS_NAME'), 'sodar-pr-project-list-item')
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
        app_settings.set(
            app_name='projectroles',
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
        self.assertEqual(
            self.selenium.find_element(
                By.ID, 'sodar-pr-project-list-message'
            ).get_attribute('style'),
            'display: none;',
        )

    def test_project_list_star_no_project(self):
        """Test project list star filter with no starred project"""
        self.login_and_redirect(self.user_owner, self.url, **self.wait_kwargs)
        self.assertEqual(self._get_item_vis_count(), 2)
        button = self.selenium.find_element(
            By.ID, 'sodar-pr-project-list-link-star'
        )
        self.assertFalse(button.is_enabled())
        button.click()

    def test_link_create_toplevel(self):
        """Test project creation link visibility"""
        expected_true = [self.superuser]
        expected_false = [
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_element_exists(
            expected_true, self.url, 'sodar-pr-home-link-create', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-pr-home-link-create', False
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


class TestProjectSidebar(ProjectInviteMixin, RemoteTargetMixin, TestUIBase):
    """Tests for the project sidebar"""

    def setUp(self):
        super().setUp()
        self.sidebar_ids = [
            'sodar-pr-nav-project-detail',
            'sodar-pr-nav-project-roles',
            'sodar-pr-nav-project-update',
        ]
        # Add app plugin navs
        for p in get_active_plugins():
            self.sidebar_ids.append('sodar-pr-nav-app-plugin-{}'.format(p.name))

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
        expected = [(self.superuser, len(get_active_plugins()))]
        self.assert_element_count(expected, url, 'sodar-pr-nav-app-plugin')

    @override_settings(PROJECTROLES_HIDE_PROJECT_APPS=['timeline'])
    def test_app_links_hide(self):
        """Test visibility of app links with timeline hidden"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected = [
            (self.superuser, len(get_active_plugins()) - 1),
            (self.user_owner, len(get_active_plugins()) - 1),
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
        expected_false = [self.user_contributor, self.user_guest]
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
        expected_false = [self.user_contributor, self.user_guest]
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
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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


class TestProjectSearchResultsView(TestUIBase):
    """Tests for ProjectSearchResultsView UI"""

    def test_search_results(self):
        """Test project search items visibility according to user permissions"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_finder_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_no_roles, 0),
        ]
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        self.assert_element_count(expected, url, 'sodar-pr-project-search-item')

    def test_search_type_project(self):
        """Test project search items visibility with 'project' type"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_finder_cat, 1),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'test type:project'})
        )
        self.assert_element_count(expected, url, 'sodar-pr-project-search-item')

    def test_search_type_nonexisting(self):
        """Test project search items visibility with a nonexisting type"""
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'test type:Jaix1au'})
        )
        self.assert_element_count(expected, url, 'sodar-pr-project-search-item')

    def test_search_project_link(self):
        """Test project link visibility according to user permissions"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_finder_cat, 0),  # This should not exist
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_no_roles, 0),
        ]
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
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
            (self.user_finder_cat, 1),  # Finder user should see this
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_no_roles, 0),
        ]
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        self.assert_element_count(
            expected, url, 'sodar-pr-project-findable', attribute='class'
        )


class TestProjectDetailView(RemoteSiteMixin, RemoteProjectMixin, TestUIBase):
    """Tests for ProjectDetailView UI"""

    @classmethod
    def _get_pr_links(cls, *args):
        """Return full IDs of project links"""
        return ['sodar-pr-link-project-' + x for x in args]

    def _setup_remote_project(
        self, site_mode=SITE_MODE_TARGET, user_visibility=True
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

        # Setup remote project pointing to local object
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
            project=self.project,
        )

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
            (self.user_owner, self._get_pr_links('roles', 'update', 'star')),
            (self.user_delegate, self._get_pr_links('roles', 'update', 'star')),
            (self.user_contributor, self._get_pr_links('roles', 'star')),
            (self.user_guest, self._get_pr_links('roles', 'star')),
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_set(expected, PROJECT_LINK_IDS, url)

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
            (self.user_finder_cat, self._get_pr_links('roles', 'star')),
            (self.user_owner, self._get_pr_links('star')),
            (self.user_delegate, self._get_pr_links('star')),
            (self.user_contributor, self._get_pr_links('star')),
            (self.user_guest, self._get_pr_links('star')),
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
        self.assert_element_set(expected, PROJECT_LINK_IDS, url)

    def test_copy_uuid_visibility_default(self):
        """Test default UUID copy button visibility (should not be visible)"""
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        for user in users:
            self.login_and_redirect(user, url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(By.ID, 'sodar-pr-btn-copy-uuid')

    def test_copy_uuid_visibility_enabled(self):
        """Test UUID copy button visibility with setting enabled"""
        app_settings.set(
            app_name='userprofile',
            setting_name='enable_project_uuid_copy',
            value=True,
            user=self.user_owner,
        )
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            [self.user_owner], url, 'sodar-pr-btn-copy-uuid', True
        )

    def test_plugin_links(self):
        """Test visibility of app plugin links"""
        expected = [(self.superuser, len(get_active_plugins()))]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-pr-link-app-plugin')

    def test_plugin_cards(self):
        """Test visibility of app plugin cards"""
        expected = [(self.superuser, len(get_active_plugins()))]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-pr-app-item')

    def test_remote_project_visible(self):
        """Test project card for enabled visbility for all users"""
        self._setup_remote_project(user_visibility=True)
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        # Visibile for all users
        for user in users:
            self.login_and_redirect(user, url)
            project_details = self.selenium.find_element(
                By.ID, 'sodar-pr-details-card-remote'
            )
            remote_project = project_details.find_element(
                By.CLASS_NAME, 'btn-info'
            )
            self.assertEqual(remote_project.text, REMOTE_SITE_NAME)

    def test_remote_project_invisible(self):
        """Test project card for disabled visibility for different users"""
        self._setup_remote_project(user_visibility=False)
        users = [self.user_delegate, self.user_contributor, self.user_guest]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        # Invisible for basic users
        for user in users:
            self.login_and_redirect(user, url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.ID, 'sodar-pr-details-card-remote'
                )
        # Greyed out for superuser and owner
        for user in [self.superuser, self.user_owner]:
            self.login_and_redirect(user, url)
            project_details = self.selenium.find_element(
                By.ID, 'sodar-pr-details-card-remote'
            )
            remote_project = project_details.find_element(
                By.CLASS_NAME, 'btn-secondary'
            )
            self.assertEqual(remote_project.text, REMOTE_SITE_NAME)

    def test_peer_project_source_invisible(self):
        """Test visibility of peer projects on SOURCE site"""
        self._setup_remote_project(site_mode=SITE_MODE_PEER)
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        for user in users:
            self.login_and_redirect(user, url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.ID, 'sodar-pr-details-card-remote'
                )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_peer_project_target_visible(self):
        """Test visibility of peer projects on TARGET site (user_display=False)"""
        # There needs to be a source mode remote project as master project,
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
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
            project=self.project,
        )
        self._setup_remote_project(site_mode=SITE_MODE_PEER)

        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]

        for user in users:
            self.login_and_redirect(user, url)
            remote_links = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(remote_links), 2)
            self.assertIn(
                'sodar-pr-link-remote-master',
                remote_links[0].get_attribute('class'),
            )
            self.assertIn(
                'sodar-pr-link-remote-peer',
                remote_links[1].get_attribute('class'),
            )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_peer_project_target_invisible(self):
        """Test invisibility of peer projects on TARGET site for users (user_display=False)"""
        # There needs to be a source mode remote project as master project,
        # otherwise peer project logic wont be reached
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
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
            project=self.project,
        )
        self._setup_remote_project(
            site_mode=SITE_MODE_PEER, user_visibility=False
        )

        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        expected_true = [self.superuser, self.user_owner_cat, self.user_owner]
        expected_false = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]

        for user in expected_true:
            self.login_and_redirect(user, url)
            remote_links = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(remote_links), 2)
            self.assertIn(
                'sodar-pr-link-remote-master',
                remote_links[0].get_attribute('class'),
            )
            self.assertIn(
                'sodar-pr-link-remote-peer',
                remote_links[1].get_attribute('class'),
            )

        for user in expected_false:
            self.login_and_redirect(user, url)
            remote_links = self.selenium.find_elements(
                By.CLASS_NAME, 'sodar-pr-link-remote'
            )
            self.assertEqual(len(remote_links), 1)
            self.assertIn(
                'sodar-pr-link-remote-master',
                remote_links[0].get_attribute('class'),
            )

    def test_archive_visibility_default(self):
        """Test archive icon and alert visibility (should not be visible)"""
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        for user in users:
            self.login_and_redirect(user, url)
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.ID, 'sodar-pr-header-icon-archive'
                )
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(By.ID, 'sodar-pr-alert-archive')

    def test_archive_visibility_archived(self):
        """Test archive icon and alert visibility for archived project"""
        self.project.set_archive()
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        for user in users:
            self.login_and_redirect(user, url)
            self.assertIsNotNone(
                self.selenium.find_element(By.ID, 'sodar-pr-alert-archive')
            )
            self.assertIsNotNone(
                self.selenium.find_element(
                    By.ID, 'sodar-pr-header-icon-archive'
                )
            )


class TestProjectCreateView(TestUIBase):
    """Tests for ProjectCreateView UI"""

    def test_owner_widget_top(self):
        """Test rendering the owner widget on the top level"""
        url = reverse('projectroles:create')
        self.assert_element_exists([self.superuser], url, 'div_id_owner', True)

    def test_owner_widget_sub(self):
        """Test rendering the owner widget under a category"""
        # Add new user, make them a contributor in category
        new_user = self.make_user('new_user')
        self.make_assignment(self.category, new_user, self.role_contributor)
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.assert_element_exists([self.superuser], url, 'div_id_owner', True)
        self.assert_element_exists(
            [self.user_owner, new_user], url, 'div_id_owner', False
        )

    def test_archive_button(self):
        """Test rendering form without archive button"""
        url = reverse('projectroles:create')
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-btn-archive', False
        )

    def test_settings_fields_default(self):
        """Test rendering of app settings fields for default view"""
        url = reverse('projectroles:create')
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertFalse(element.is_displayed())

    def test_settings_fields_project(self):
        """Test rendering of app settings fields for project creation"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertFalse(element.is_displayed())
        select = Select(
            self.selenium.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_type"] div select[id="id_type"]',
            )
        )
        select.select_by_value('PROJECT')
        self.assertEqual(select.first_selected_option.text, 'Project')
        WebDriverWait(self.selenium, 10)
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertTrue(element.is_displayed())

    def test_settings_fields_category(self):
        """Test rendering of app settings fields for category creation"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertFalse(element.is_displayed())
        select = Select(
            self.selenium.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_type"] div select[id="id_type"]',
            )
        )
        select.select_by_value('CATEGORY')
        self.assertEqual(select.first_selected_option.text, 'Category')
        WebDriverWait(self.selenium, 10)
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertFalse(element.is_displayed())

    def test_settings_label_icon(self):
        """Test rendering of app settings icon for project creation"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        select = Select(
            self.selenium.find_element(
                By.CSS_SELECTOR,
                'div[id="div_id_type"] div select[id="id_type"]',
            )
        )
        select.select_by_value('PROJECT')
        WebDriverWait(self.selenium, 10)
        logo = self.selenium.find_element(
            By.CSS_SELECTOR,
            'div[id="div_id_settings.example_project_app.project_int_setting"]',
        ).find_element(By.TAG_NAME, 'svg')
        self.assertTrue(logo.is_displayed())


class TestProjectUpdateView(TestUIBase):
    """Tests for ProjectUpdateView UI"""

    def test_archive_button(self):
        """Test rendering of archive button"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-btn-archive', True
        )
        element = self.selenium.find_element(By.ID, 'sodar-pr-btn-archive')
        self.assertEqual(element.text, 'Archive')

    def test_archive_button_archived(self):
        """Test rendering of archive button with archived project"""
        self.project.set_archive()
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            [self.superuser], url, 'sodar-pr-btn-archive', True
        )
        element = self.selenium.find_element(By.ID, 'sodar-pr-btn-archive')
        self.assertEqual(element.text, 'Unarchive')

    def test_settings_fields_project_update(self):
        """Test rendering of app settings fields for project update view"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertTrue(element.is_displayed())

    def test_settings_fields_category_update(self):
        """Test rendering of app settings fields for category update view"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )
        self.login_and_redirect(
            self.superuser, url, wait_elem=None, wait_loc='ID'
        )
        element = self.selenium.find_element(
            By.ID, 'div_id_settings.example_project_app.project_int_setting'
        )
        self.assertFalse(element.is_displayed())


class TestProjectArchiveView(TestUIBase):
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


class TestProjectRoleView(RemoteTargetMixin, TestUIBase):
    """Tests for ProjectRoleView UI"""

    def _get_role_dropdown(self, user):
        """Return role dropdown for a user"""
        row = self.selenium.find_element(
            By.XPATH,
            '//tr[@class="sodar-pr-role-list-row" and '
            '@data-user-uuid="{}"]'.format(user.sodar_uuid),
        )
        return row.find_element(By.CLASS_NAME, 'sodar-pr-role-dropdown')

    def _get_role_links(self, user):
        """Return role dropdown links for a user"""
        dropdown = self._get_role_dropdown(user)
        return dropdown.find_elements(By.CLASS_NAME, 'dropdown-item')

    def setUp(self):
        super().setUp()
        self.user_assign = self.make_user('user_assign')
        self.url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )

    def test_list_buttons(self):
        """Test visibility of role list button group"""
        good_users = [self.superuser, self.user_owner, self.user_delegate]
        bad_users = [self.user_contributor, self.user_guest]
        self.assert_element_exists(
            good_users, self.url, 'sodar-pr-btn-role-op', True
        )
        self.assert_element_exists(
            bad_users, self.url, 'sodar-pr-btn-role-op', False
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_list_buttons_target(self):
        """Test visibility of role list button group as target"""
        # Set up site as target
        self.set_up_as_target(projects=[self.category, self.project])
        non_superusers = [
            self.user_owner,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        self.login_and_redirect(self.superuser, self.url)
        btn = self.selenium.find_element(By.ID, 'sodar-pr-btn-role-op')
        self.assertEqual(btn.is_enabled(), False)
        self.assert_element_exists(
            non_superusers, self.url, 'sodar-pr-btn-role-op', False
        )

    def test_role_list_invite_button(self):
        """Test visibility of role invite button"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
        ]
        self.assert_element_exists(
            expected_true, self.url, 'sodar-pr-btn-role-list-invite', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-pr-btn-role-list-invite', False
        )

    def test_role_list_add_button(self):
        """Test visibility of role invite button"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
        ]
        self.assert_element_exists(
            expected_true, self.url, 'sodar-pr-btn-role-list-create', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-pr-btn-role-list-create', False
        )

    def test_role_buttons(self):
        """Test visibility of role management buttons"""
        expected = [
            (self.superuser, 6),
            (self.user_owner_cat, 6),
            (self.user_delegate_cat, 4),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 6),
            (self.user_delegate, 4),
            (self.user_contributor, 0),
            (self.user_guest, 0),
        ]
        self.assert_element_count(expected, self.url, 'sodar-pr-btn-grp-role')

    def test_role_links_owner_local(self):
        """Test role dropdown links for local owner"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self._get_role_dropdown(self.user_owner)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-transfer')
        )
        # TODO: Assert link enabling/disabling after updating owner transfer

    def test_role_links_owner_inherited(self):
        """Test role dropdown links for inherited owner"""
        # Set category owner to new user
        self.owner_as_cat.user = self.user_assign
        self.owner_as_cat.save()
        self.login_and_redirect(self.superuser, self.url)
        with self.assertRaises(NoSuchElementException):
            self._get_role_dropdown(self.user_assign)

    def test_role_links_delegate_local(self):
        """Test role dropdown links for local delegate"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self._get_role_dropdown(self.user_delegate)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-update')
        )
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-delete')
        )

    def test_role_links_delegate_inherited(self):
        """Test role dropdown links for inherited delegate"""
        self.login_and_redirect(self.superuser, self.url)
        with self.assertRaises(NoSuchElementException):
            self._get_role_dropdown(self.user_delegate_cat)

    def test_role_links_contrib_local(self):
        """Test role dropdown links for local contributor"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self._get_role_dropdown(self.user_contributor)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-update')
        )
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-delete')
        )

    def test_role_links_contrib_inherited(self):
        """Test role dropdown links for inherited contributor"""
        self.make_assignment(
            self.category, self.user_assign, self.role_contributor
        )
        self.login_and_redirect(self.superuser, self.url)
        elem = self._get_role_dropdown(self.user_assign)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-promote')
        )
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-update')
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-delete')

    def test_role_links_guest_local(self):
        """Test role dropdown links for local guest"""
        self.login_and_redirect(self.superuser, self.url)
        elem = self._get_role_dropdown(self.user_guest)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-update')
        )
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-delete')
        )

    def test_role_links_guest_inherited(self):
        """Test role dropdown links for inherited guest"""
        self.make_assignment(self.category, self.user_assign, self.role_guest)
        self.login_and_redirect(self.superuser, self.url)
        elem = self._get_role_dropdown(self.user_assign)
        self.assertIsNotNone(
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-promote')
        )
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-update')
        with self.assertRaises(NoSuchElementException):
            elem.find_element(By.CLASS_NAME, 'sodar-pr-role-link-delete')


class TestRoleAssignmentCreateView(TestUIBase):
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


class TestRoleAssignmentDeleteView(TestUIBase):
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


class TestProjectInviteView(ProjectInviteMixin, TestUIBase):
    """Tests for ProjectInviteView UI"""

    def test_list_buttons(self):
        """Test visibility of invite list button group"""
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
            expected_true, url, 'sodar-pr-btn-role-list', True
        )

    def test_role_list_invite_button(self):
        """Test visibility of role invite button"""
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
            expected_true, url, 'sodar-pr-btn-role-list-invite', True
        )

    def test_role_list_add_button(self):
        """Test visibility of role invite button"""
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
            expected_true, url, 'sodar-pr-btn-role-list-create', True
        )

    def test_invite_buttons(self):
        """Test visibility of invite management buttons"""
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
        self.assert_element_count(expected, url, 'sodar-pr-btn-grp-invite')


class TestProjectInviteCreateView(TestUIBase):
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


class TestRemoteSiteListView(RemoteSiteMixin, TestUIBase):
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


class TestRemoteSiteCreateView(RemoteSiteMixin, TestUIBase):
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
        self.assertFalse(
            self.selenium.find_element(By.ID, 'id_user_display').is_displayed()
        )
