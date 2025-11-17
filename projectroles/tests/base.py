"""UI view tests for the projectroles app"""

import base64
import socket


from datetime import datetime
from typing import Optional, Union
from urllib.parse import quote
from zoneinfo import ZoneInfo

from django.apps import apps
from django.conf import settings
from django.contrib.auth import (
    get_user_model,
    SESSION_KEY,
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
)
from django.contrib.sessions.backends.db import SessionStore
from django.db.models import QuerySet
from django.http import HttpResponse
from django.test import LiveServerTestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from test_plus.test import TestCase, APITestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
)
from projectroles.plugins import PluginAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    AppSettingMixin,
)


app_settings = AppSettingAPI()
plugin_api = PluginAPI()
User = get_user_model()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
APP_NAME = 'projectroles'
AUTHENTICATION_BACKENDS_AXES = [
    'axes.backends.AxesBackend'
] + settings.AUTHENTICATION_BACKENDS
AXES_LOCK_MSG = 'Account locked: too many login attempts.'
EMPTY_KNOX_TOKEN = '__EmpTy_KnoX_tOkEn_FoR_tEsT_oNlY_0xDEADBEEF__'
TEST_SERVER_URL = 'http://testserver'
DEFAULT_WAIT_LOC = 'ID'
TEST_BASE_CLASS_DEPRECATE_MSG = (
    '\nWARNING: {old} has been deprecated and will be removed in v1.4. Use '
    'projectroles.tests.base.{new} instead.'
)  # TODO: Remove in v1.4 (see #1830)


# UI View Test Base Classes ----------------------------------------------------


class UIViewTestBase(RoleMixin, TestCase):
    """Base class for view testing"""

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()


# REST API View Test Base Classes ----------------------------------------------


class SerializedObjectMixin:
    """
    Mixin for helpers with serialized objects.
    """

    @classmethod
    def get_serialized_user(cls, user: User, auth_type: bool = True) -> dict:
        """
        Return serialization for a user.

        :param user: User object
        :param auth_type: Include user auth type if True (bool)
        :return: Dict
        """
        add_emails = SODARUserAdditionalEmail.objects.filter(
            user=user, verified=True
        ).order_by('email')
        ret = {
            'additional_emails': [e.email for e in add_emails],
            'email': user.email,
            'is_superuser': user.is_superuser,
            'name': user.name,
            'sodar_uuid': str(user.sodar_uuid),
            'username': user.username,
        }
        if auth_type:
            ret['auth_type'] = user.get_auth_type()
        return ret


class SODARAPIViewTestMixin(SerializedObjectMixin):
    """
    Mixin for SODAR and SODAR Core API views with accept headers, knox token
    authorization and general helper methods.
    """

    # Set client class to drf API client to work with PUT, see #1801
    client_class = APIClient

    @classmethod
    def get_basic_auth_header(cls, username: str, password: str) -> dict:
        """
        Return basic authorization header for requests.

        :param username: String
        :param password: String
        :return: Dict
        """
        v = base64.b64encode(f'{username}:{password}'.encode('ascii')).decode()
        return {'HTTP_AUTHORIZATION': f'Basic {v}'}

    @classmethod
    def get_token(
        cls, user: User, full_result: bool = False
    ) -> Union[str, tuple]:
        """
        Get or create an authentication token for a user.

        NOTE: Requires KNOX_AUTH_TOKEN to be set.

        :param user: User object
        :param full_result: Return full result of token creation if True
        :return: Token string or knox-compatible token creation tuple
                 (EMPTY_KNOX_TOKEN if user is None)
        """
        if user is None:
            return EMPTY_KNOX_TOKEN
        model_split = settings.KNOX_TOKEN_MODEL.split('.')
        token_model = apps.get_model(model_split[0], model_split[1])
        result = token_model.objects.create(user=user)
        return result if full_result else result[1]

    @classmethod
    def get_drf_datetime(cls, obj_dt: datetime) -> str:
        """
        Return datetime in DRF compatible format.

        :param obj_dt: Object DateTime field
        :return: String
        """
        return timezone.localtime(
            obj_dt, ZoneInfo(settings.TIME_ZONE)
        ).isoformat()

    @classmethod
    def get_accept_header(
        cls,
        media_type: Optional[str] = None,
        version: Optional[str] = None,
    ) -> dict:
        """
        Return version accept header based on the media type and version string.

        :param media_type: String (default = cls.media_type)
        :param version: String (default = cls.api_version)
        :return: Dict
        """
        if not media_type:
            media_type = cls.media_type
        if not version:
            version = cls.api_version
        return {'HTTP_ACCEPT': f'{media_type}; version={version}'}

    @classmethod
    def get_token_header(cls, token: str) -> dict:
        """
        Return auth header based on token.

        :param token: Token string
        :return: Dict, empty if token is None
        """
        if token is EMPTY_KNOX_TOKEN:
            return {}
        return {'HTTP_AUTHORIZATION': f'token {token}'}

    def request_knox(
        self,
        url: str,
        method: str = 'GET',
        format: str = 'json',
        data: Optional[dict] = None,
        token: Optional[str] = None,
        media_type: Optional[str] = None,
        version: Optional[str] = None,
        header: Optional[dict] = None,
    ) -> HttpResponse:
        """
        Perform a HTTP request with Knox token auth.

        :param url: URL for the request
        :param method: Request method (string, default="GET")
        :param format: Request format (string, default="json")
        :param data: Optional data for request (dict)
        :param token: Knox token string (if None, use self.knox_token)
        :param media_type: String (default = cls.media_type)
        :param version: String (default = cls.api_version)
        :param header: Optional header data (dict)
        :return: Response object
        """
        if not token:
            token = self.knox_token
        req_kwargs = {
            'format': format,
            **self.get_accept_header(media_type, version),
            **self.get_token_header(token),
        }
        if data:
            req_kwargs['data'] = data
        if header:
            req_kwargs.update(header)
        req_method = getattr(self.client, method.lower(), None)
        if not req_method:
            raise ValueError(f'Unsupported method "{method}"')
        return req_method(url, **req_kwargs)


class APIViewTestBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    SODARAPIViewTestMixin,
    APITestCase,
):
    """Base API test view with knox authentication"""

    def setUp(self):
        # Show complete diff in case of failure
        self.maxDiff = None
        # Init roles
        self.init_roles()

        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        # Init project users
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_owner = self.make_user('user_owner')

        # Set up category and project with owner role assignments
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Get knox token for self.user
        self.knox_token = self.get_token(self.user)


# Permission Test Base Classes -------------------------------------------------


class PermissionTestMixin:
    """Helper class for permission tests"""

    def setup_user_helpers(self):
        """
        Set up user helpers for easy reference to specific groups.

        NOTE: Expects the users having set up in the class beforehand.
        """
        self.all_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]  # All users
        # All authenticated users
        self.auth_users = self.all_users[:-1]
        # All users except for superuser
        self.non_superusers = self.all_users[1:]
        # All authenticated non-superusers
        self.auth_non_superusers = self.non_superusers[:-1]
        # No roles user and anonymous user
        self.no_role_users = [self.user_no_roles, self.anonymous]

    def set_site_read_only(self, value: bool = True):
        """
        Set site read only mode to the desired value.

        :param value: Boolean
        """
        app_settings.set(APP_NAME, 'site_read_only', value)

    def set_access_block(self, project: Project, value: bool = True):
        """
        Set project access block to the desired value.

        :param project: Project object
        :param value: Boolean
        """
        app_settings.set(
            APP_NAME, 'project_access_block', value, project=project
        )

    def set_category_public_stats(self, category: Project, value: bool = True):
        """
        Set category_public_stats app setting value for top level category.

        :param category: Project object (must be top level category)
        :param value: Boolean
        """
        if category.is_project() or category.parent:
            raise ValueError('This is only allowed for top level categories')
        app_settings.set(
            APP_NAME, 'category_public_stats', value, project=category
        )

    def send_request(
        self, url: str, method: str, req_kwargs: dict
    ) -> HttpResponse:
        req_method = getattr(self.client, method.lower(), None)
        if not req_method:
            raise ValueError(f'Invalid method "{method}"')
        return req_method(url, **req_kwargs)

    def assert_response(
        self,
        url: str,
        users: Union[list, tuple, User],
        status_code: int,
        redirect_user: Optional[str] = None,
        redirect_anon: Optional[str] = None,
        method: str = 'GET',
        data: Optional[dict] = None,
        header: Optional[dict] = None,
        cleanup_method: Optional[callable] = None,
        req_kwargs: Optional[dict] = None,
    ):
        """
        Assert a response status code for url with a list of users. Also checks
        for redirection URL where applicable.

        :param url: Target URL for the request
        :param users: Users to test (single user, list or tuple)
        :param status_code: Status code
        :param redirect_user: Redirect URL for signed in user (optional)
        :param redirect_anon: Redirect URL for anonymous (optional)
        :param method: Method for request (string, optional, default='GET')
        :param data: Optional data for request (dict, optional)
        :param header: Request header (dict, optional)
        :param cleanup_method: Callable method to clean up data after a
               successful request
        :param req_kwargs: Optional request kwargs override (dict or None)
        """
        if header is None:
            header = {}
        if not isinstance(users, (list, tuple)):
            users = [users]

        for user in users:
            req_kwargs = req_kwargs if req_kwargs else {}
            if data:
                req_kwargs.update({'data': data})
            if header:
                req_kwargs.update(header)

            if user:  # Authenticated user
                re_url = redirect_user if redirect_user else reverse('home')
                with self.login(user):
                    response = self.send_request(url, method, req_kwargs)
            else:  # Anonymous
                if redirect_anon:
                    re_url = redirect_anon
                else:
                    url_split = url.split('?')
                    if len(url_split) > 1:
                        next_url = url_split[0] + quote('?' + url_split[1])
                    else:
                        next_url = url
                    re_url = reverse('login') + '?next=' + next_url
                response = self.send_request(url, method, req_kwargs)

            msg = f'user={user}'
            self.assertEqual(response.status_code, status_code, msg=msg)
            if status_code == 302:
                self.assertEqual(response.url, re_url, msg=msg)
            if cleanup_method:
                cleanup_method()


class IPAllowMixin(AppSettingMixin):
    """Mixin for IP allowing test helpers"""

    def setup_ip_allowing(self, ip_list: list[str] = []):
        # Init IP restrict setting
        self.make_setting(
            plugin_name=APP_NAME,
            name='ip_restrict',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
        )
        # Init IP allowlist setting
        self.make_setting(
            plugin_name=APP_NAME,
            name='ip_allow_list',
            setting_type=APP_SETTING_TYPE_STRING,
            value=','.join(ip_list),
            value_json=None,
            project=self.project,
        )


class PermissionTestBase(PermissionTestMixin, TestCase):
    """
    Base class for permission tests for UI views.

    NOTE: For REST API views, you need to use APITestCase
    """


class ProjectPermissionTestBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    PermissionTestBase,
):
    """
    Base class for testing project permissions.

    NOTE: For REST API views, you need to use APITestCase.
    """

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init users
        # Superuser
        self.superuser = self.make_user('superuser')
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        # No user
        self.anonymous = None
        # Users with role assignments
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_delegate_cat = self.make_user('user_delegate_cat')
        self.user_contributor_cat = self.make_user('user_contributor_cat')
        self.user_viewer_cat = self.make_user('user_viewer_cat')
        self.user_guest_cat = self.make_user('user_guest_cat')
        self.user_finder_cat = self.make_user('user_finder_cat')
        self.user_owner = self.make_user('user_owner')
        self.user_delegate = self.make_user('user_delegate')
        self.user_contributor = self.make_user('user_contributor')
        self.user_guest = self.make_user('user_guest')
        self.user_viewer = self.make_user('user_viewer')
        # User without role assignments
        self.user_no_roles = self.make_user('user_no_roles')

        # Init projects
        # Top level category
        self.category = self.make_project(
            title='TestCategory', type=PROJECT_TYPE_CATEGORY, parent=None
        )
        # Subproject under category
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
        self.viewer_as_cat = self.make_assignment(
            self.category, self.user_viewer_cat, self.role_viewer
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
        self.viewer_as = self.make_assignment(
            self.project, self.user_viewer, self.role_viewer
        )
        # Set up user helpers
        self.setup_user_helpers()


class SiteAppPermissionTestBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    PermissionTestBase,
):
    """Base class for testing site app permissions"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        # No user
        self.anonymous = None


# REST API Permission Test Base Classes ----------------------------------------


class SODARAPIPermissionTestMixin(SODARAPIViewTestMixin):
    """Mixin for permission testing with knox auth"""

    def assert_response_api(
        self,
        url: str,
        users: Union[list, tuple, User],
        status_code: int,
        method: str = 'GET',
        format: str = 'json',
        data: Optional[dict] = None,
        media_type: Optional[str] = None,
        version: Optional[str] = None,
        knox: bool = False,
        cleanup_method: Optional[callable] = None,
        cleanup_kwargs: Optional[dict] = None,
        req_kwargs: Optional[dict] = None,
    ):
        """
        Assert a response status code for url with API headers and optional
        Knox token authentication. Creates a Knox token for each user where
        needed.

        :param url: Target URL for the request
        :param users: Users to test (single user, list or tuple)
        :param status_code: Status code
        :param method: Method for request (default="GET")
        :param format: Request format (string, default="json")
        :param data: Optional data for request (dict)
        :param media_type: String (default = cls.media_type)
        :param version: String (default = cls.api_version)
        :param knox: Use Knox token auth instead of Django login (boolean)
        :param cleanup_method: Callable method to clean up data after a
               successful request
        :param cleanup_kwargs: Optional cleanup method kwargs (dict or None)
        :param req_kwargs: Optional request kwargs override (dict or None)
        """
        if cleanup_method and not callable(cleanup_method):
            raise ValueError('cleanup_method is not callable')

        def _send_request() -> HttpResponse:
            req_method = getattr(self.client, method.lower(), None)
            if not req_method:
                raise ValueError(f'Invalid method "{method}"')
            if req_kwargs:  # Override request kwargs if set
                r_kwargs.update(req_kwargs)
            return req_method(url, **r_kwargs)

        if not isinstance(users, (list, tuple)):
            users = [users]

        for user in users:
            r_kwargs = {'format': format}
            if data:
                r_kwargs['data'] = data
            if knox and not user:  # Anonymous
                raise ValueError(
                    'Unable to test Knox token auth with anonymous user'
                )
            r_kwargs.update(self.get_accept_header(media_type, version))

            if knox:
                r_kwargs.update(self.get_token_header(self.get_token(user)))
                response = _send_request()
            elif user:
                with self.login(user):
                    response = _send_request()
            else:  # Anonymous, no knox
                response = _send_request()

            msg = f'user={user}; content="{response.content}"'
            self.assertEqual(response.status_code, status_code, msg=msg)

            if cleanup_method:
                if cleanup_kwargs is None:
                    cleanup_kwargs = {}
                cleanup_method(**cleanup_kwargs)


class ProjectAPIPermissionTestBase(
    SODARAPIPermissionTestMixin, APITestCase, ProjectPermissionTestBase
):
    """Base class for testing project permissions in SODAR API views"""


# UI Test Base Classes ---------------------------------------------------------


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
        options.add_argument(
            f'--window-size={self.window_size[0]},{self.window_size[1]}'
        )
        # Disable password warnings which make certain tests fail
        options.add_experimental_option(
            'prefs', {'profile.password_manager_leak_detection': False}
        )
        self.selenium = webdriver.Chrome(options=options)


class LiveUserMixin:
    """Mixin for creating users to work with LiveServerTestCase"""

    @classmethod
    def make_user(cls, user_name: str, superuser: bool = False) -> User:
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
        user: User,
        url: str,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
    ):
        """
        Login with Selenium by setting a cookie, wait for redirect to given URL.

        If PROJECTROLES_TEST_UI_LEGACY_LOGIN=True, use legacy UI login method.

        :param user: User object
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
        user: User,
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
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.element_to_be_clickable(user_button)
            )
            user_button.click()
            # Wait for element to be visible
            WebDriverWait(self.selenium, self.wait_time).until(
                ec.presence_of_element_located(
                    (By.ID, 'sodar-navbar-user-legend')
                )
            )
            try:
                logout_btn = self.selenium.find_element(
                    By.ID, 'sodar-navbar-link-logout'
                )
                WebDriverWait(self.selenium, self.wait_time).until(
                    ec.element_to_be_clickable(logout_btn)
                )
                logout_btn.click()
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
        WebDriverWait(
            self.selenium,
            self.wait_time,
            ignored_exceptions=(StaleElementReferenceException),
        ).until(
            ec.element_to_be_clickable((By.ID, 'sodar-navbar-user-dropdown'))
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
        users: Union[list[User], QuerySet[User]],
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
        user: User,
        element_id: str,
        all_elements: list[str],
        url: str,
        wait_elem: Optional[str] = None,
        wait_loc: str = DEFAULT_WAIT_LOC,
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
    SeleniumSetupMixin, LiveUserMixin, UITestMixin, LiveServerTestCase
):
    """Common base class for view specific UI test base classes"""

    def setUp(self):
        # Set up Selenium
        self.set_up_selenium()
        # Init superuser
        self.superuser = self.make_user('superuser', superuser=True)

    def tearDown(self):
        # Shut down Selenium
        self.selenium.quit()
        super().tearDown()


class SiteUITestBase(UITestBase):
    """Base class for site app view UI tests"""

    def setUp(self):
        super().setUp()
        self.regular_user = self.make_user('regular_user')


class ProjectUITestBase(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, UITestBase
):
    """Base class for project app view UI tests"""

    def setUp(self):
        super().setUp()
        # Init roles
        self.init_roles()
        # Init users
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
