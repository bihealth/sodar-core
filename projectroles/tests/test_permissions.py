"""Tests for UI view permissions in the projectroles app"""

from typing import Optional, Union
from urllib.parse import urlencode, quote

from django.http import HttpResponse
from django.test import override_settings
from django.urls import reverse

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import Project, SODARUser, SODAR_CONSTANTS
from projectroles.utils import build_secret
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
)


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
APP_NAME = 'projectroles'
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_SECRET = build_secret()


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
        users: Union[list, tuple, SODARUser],
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


class TestGeneralViews(ProjectPermissionTestBase):
    """Tests for general non-project UI view permissions"""

    def test_get_home(self):
        """Test HomeView GET"""
        url = reverse('home')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_home_anon(self):
        """Test HomeView GET with anonymous access"""
        url = reverse('home')
        self.assert_response(url, self.all_users, 200)

    def test_get_home_read_only(self):
        """Test HomeView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('home')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_search(self):
        """Test ProjectSearchResultsView GET"""
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_search_anon(self):
        """Test ProjectSearchResultsView GET with anonymous access"""
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        self.assert_response(url, self.all_users, 200)

    def test_get_search_read_only(self):
        """Test ProjectSearchResultsView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 302)

    def test_get_search_advanced(self):
        """Test ProjectAdvancedSearchView GET"""
        url = reverse('projectroles:search_advanced')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_search_advanced_anon(self):
        """Test ProjectAdvancedSearchView GET with anonymous access"""
        url = reverse('projectroles:search_advanced')
        self.assert_response(url, self.all_users, 200)

    def test_get_login(self):
        """Test LoginView GET"""
        url = reverse('login')
        self.assert_response(url, self.all_users, 200)

    def test_get_logout(self):
        """Test logout view GET"""
        url = reverse('logout')
        self.assert_response(
            url,
            self.auth_users,
            302,
            redirect_user='/login/',
            redirect_anon='/login/',
        )

    def test_get_admin(self):
        """Test admin view GET"""
        url = '/admin/'
        self.assert_response(url, self.superuser, 200)
        self.assert_response(
            url,
            self.non_superusers,
            302,
            redirect_user='/admin/login/?next=/admin/',
            redirect_anon='/admin/login/?next=/admin/',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_admin_anon(self):
        """Test admin view GET with anonymous access"""
        url = '/admin/'
        self.assert_response(url, self.superuser, 200)
        self.assert_response(
            url,
            self.non_superusers,
            302,
            redirect_user='/admin/login/?next=/admin/',
            redirect_anon='/admin/login/?next=/admin/',
        )


class TestProjectDetailView(ProjectPermissionTestBase):
    """Tests for ProjectDetailView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users = [
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
        self.bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
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
        self.bad_users_cat = self.no_role_users

    def test_get(self):
        """Test ProjectDetailView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        # Test public project
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, [self.user_finder_cat, self.user_no_roles], 200
            )
            self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.bad_users, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, [self.user_finder_cat, self.user_no_roles], 200
            )
            self.assert_response(self.url, self.anonymous, 302)

    def test_get_block(self):
        """Test GET with blocked project"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_public_block_anon(self):
        """Test GET with blocked public access project with anonymous access"""
        self.set_access_block(self.project)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)
        # Test with public access to child project enabled
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, [self.user_finder_cat, self.user_no_roles], 200
            )
            self.assert_response(self.url_cat, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.auth_users, 200)
        self.assert_response(self.url_cat, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.anonymous, 200)


class TestProjectCreateView(ProjectPermissionTestBase):
    """Tests for ProjectCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url_top = reverse('projectroles:create')
        self.url_cat = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users_top = [self.superuser]
        self.bad_users_top = [
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
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
        ]
        self.bad_users_cat = [
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
        ]

    def test_get_top(self):
        """Test ProjectCreateView GET for top level creation"""
        self.assert_response(self.url_top, self.good_users_top, 200)
        self.assert_response(self.url_top, self.bad_users_top, 302)

    def test_get_top_read_only(self):
        """Test GET for top level with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_top, self.good_users_top, 200)
        self.assert_response(self.url_top, self.bad_users_top, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        # Only superuser should have access in read-only mode
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestProjectUpdateView(ProjectPermissionTestBase):
    """Tests for ProjectUpdateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_cat = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectUpdateView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)
        # Set project public, ensure category access
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access for project"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestProjectArchiveView(ProjectPermissionTestBase):
    """Tests for ProjectArchiveView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:archive', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:archive', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.bad_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_non_cat = [
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
        ]

    def test_get(self):
        """Test ProjectArchiveView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(
            self.url_cat,
            self.bad_users_cat,
            302,
            redirect_user=reverse(
                'projectroles:detail',
                kwargs={'project': self.category.sodar_uuid},
            ),
        )
        self.assert_response(
            self.url_cat,
            self.bad_users_non_cat,
            302,  # Non-category users get redirected to home
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(
            self.url_cat,
            self.bad_users_cat,
            302,
            redirect_user=reverse(
                'projectroles:detail',
                kwargs={'project': self.category.sodar_uuid},
            ),
        )
        self.assert_response(
            self.url_cat,
            self.bad_users_non_cat,
            302,  # Non-category users get redirected to home
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestProjectDeleteView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectPermissionTestBase
):
    """Tests for ProjectDeleteView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:delete', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:delete', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectDeleteView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category_with_children(self):
        """Test GET with category and children"""
        self.assert_response(self.url_cat, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_no_children(self):
        """Test GET with category and no children"""
        self.project.delete()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
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
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_no_children_public_stats(self):
        """Test GET with category, no children and public stats"""
        self.set_category_public_stats(self.category)
        self.project.delete()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
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
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_no_children_public_stats_anon(self):
        """Test GET with category, no children, public stats and anon access"""
        self.set_category_public_stats(self.category)
        self.project.delete()
        self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.project.delete()
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_remote_not_revoked(self):
        """Test GET with non-revoked remote project"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.assert_response(self.url, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_remote_revoked(self):
        """Test GET with revoked remote project"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED'],
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_remote_not_revoked_target(self):
        """Test GET with non-revoked remote project as target site"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.assert_response(self.url, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_get_remote_revoked_target(self):
        """Test GET with revoked remote project as target site"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED'],
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)


class TestProjectRoleView(ProjectPermissionTestBase):
    """Tests for ProjectRoleView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:roles', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users = [
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
        self.bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
        ]
        self.bad_users_cat = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectRoleView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, [self.user_finder_cat, self.user_no_roles], 200
            )
            self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, [self.user_finder_cat, self.user_no_roles], 200
            )
            self.assert_response(self.url, self.anonymous, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        # View should still be browseable
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, [self.user_finder_cat, self.user_no_roles], 200
            )
            self.assert_response(self.url, self.anonymous, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestRoleAssignmentCreateView(ProjectPermissionTestBase):
    """Tests for RoleAssignmentCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:role_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_cat = [
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
        ]

    def test_get(self):
        """Test RoleAssignmentCreateView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestRoleAssignmentUpdateView(ProjectPermissionTestBase):
    """Tests for RoleAssignmentUpdateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as_cat.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_cat = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test RoleAssignmentUpdateView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_owner(self):
        """Test GET with owner role (should fail)"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.assert_response(url, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_owner_anon(self):
        """Test GET with owner role with anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)

    def test_get_delegate(self):
        """Test GET with delegate role"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
        ]
        bad_users = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)


class TestRoleAssignmentDeleteView(ProjectPermissionTestBase):
    """Tests for RoleAssignmentDeleteView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as_cat.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_cat = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test RoleAssignmentDeleteView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_owner(self):
        """Test GET with owner role (should fail)"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.assert_response(url, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_owner_anon(self):
        """Test GET with owner role and anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)

    def test_get_delegate(self):
        """Test GET with delegate role"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
        ]
        bad_users = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)


class TestRoleAssignmentOwnDeleteView(ProjectPermissionTestBase):
    """Tests for RoleAssignmentOwnDeleteView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:role_delete_own',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:role_delete_own',
            kwargs={'roleassignment': self.contributor_as_cat.sodar_uuid},
        )

    def test_get(self):
        """Test RoleAssignmentOwnDeleteView GET"""
        good_users = [self.user_contributor]
        bad_users = [u for u in self.all_users if u != self.user_contributor]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        good_users = [self.user_contributor]
        bad_users = [u for u in self.all_users if u != self.user_contributor]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.all_users, 302)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [self.user_contributor_cat]
        bad_users = [
            u for u in self.all_users if u != self.user_contributor_cat
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.all_users, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        good_users = [self.user_contributor_cat]
        bad_users = [
            u for u in self.all_users if u != self.user_contributor_cat
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_owner(self):
        """Test GET with owner role (should fail)"""
        url = reverse(
            'projectroles:role_delete_own',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.assert_response(url, self.all_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(url, self.no_role_users, 302)


class TestRoleAssignmentOwnerTransferView(ProjectPermissionTestBase):
    """Tests for RoleAssignmentOwnerTransferView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:role_owner_transfer',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
        ]
        self.bad_users = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
        ]
        self.bad_users_cat = [
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test RoleAssignmentOwnerTransferView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access (should fail)"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url_cat, self.no_role_users, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestProjectInviteView(ProjectPermissionTestBase):
    """Tests for ProjectInviteView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:invites', kwargs={'project': self.category.sodar_uuid}
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_cat = [
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
        ]

    def test_get(self):
        """Test ProjectInviteView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestProjectInviteCreateView(ProjectPermissionTestBase):
    """Tests for ProjectInviteCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.good_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        self.bad_users_cat = [
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
        ]

    def test_get(self):
        """Test ProjectInviteCreateView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200)
        self.assert_response(self.url_cat, self.non_superusers, 302)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response(self.url_cat, self.no_role_users, 302)


class TestProjectInviteResendView(ProjectPermissionTestBase):
    """Tests for ProjectInviteResendView permissions"""

    def setUp(self):
        super().setUp()
        # Init invite
        invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        self.url = reverse(
            'projectroles:invite_resend',
            kwargs={'projectinvite': invite.sodar_uuid},
        )
        self.url_redirect_good = reverse(
            'projectroles:invites',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_redirect_bad = reverse('home')
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectInviteResendView GET"""
        self.assert_response(
            self.url,
            self.good_users,
            302,
            redirect_user=self.url_redirect_good,
        )
        self.assert_response(
            self.url, self.bad_users, 302, redirect_user=self.url_redirect_bad
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url,
                self.no_role_users,
                302,
                redirect_user=self.url_redirect_bad,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url,
                self.no_role_users,
                302,
                redirect_user=self.url_redirect_bad,
            )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(
            self.url,
            self.good_users,
            302,
            redirect_user=self.url_redirect_good,
        )
        self.assert_response(
            self.url, self.bad_users, 302, redirect_user=self.url_redirect_bad
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url,
                self.no_role_users,
                302,
                redirect_user=self.url_redirect_bad,
            )

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(
            self.url,
            self.superuser,
            302,
            redirect_user=self.url_redirect_good,
        )
        self.assert_response(
            self.url,
            self.non_superusers,
            302,
            redirect_user=self.url_redirect_bad,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url,
                self.non_superusers,
                302,
                redirect_user=self.url_redirect_bad,
            )


class TestProjectInviteRevokeView(ProjectPermissionTestBase):
    """Tests for ProjectInviteRevokeView permissions"""

    def setUp(self):
        super().setUp()
        # Init invite
        invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        self.url = reverse(
            'projectroles:invite_revoke',
            kwargs={'projectinvite': invite.sodar_uuid},
        )
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test ProjectInviteRevokeView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.no_role_users, 302)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(self.url, self.non_superusers, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)


class TestSiteAppSettingsFormView(ProjectPermissionTestBase):
    """Tests for SiteAppSettingsFormView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:site_app_settings')

    def test_get(self):
        """Test SiteAppSettingsFormView GET"""
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200)
        self.assert_response(self.url, self.non_superusers, 302)


class TestRemoteSiteViews(RemoteSiteMixin, SiteAppPermissionTestBase):
    """Tests for UI view permissions in remote site views"""

    def setUp(self):
        super().setUp()
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

    def test_get_remote_sites(self):
        """Test RemoteSiteListView GET"""
        url = reverse('projectroles:remote_sites')
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_remote_site_create(self):
        """Test RemoteSiteCreateView GET"""
        url = reverse('projectroles:remote_site_create')
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_remote_site_update(self):
        """Test RemoteSiteUpdateView GET"""
        url = reverse(
            'projectroles:remote_site_update',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_remote_site_delete(self):
        """Test RemoteSiteDeleteView GET"""
        url = reverse(
            'projectroles:remote_site_delete',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_remote_projects(self):
        """Test RemoteProjectListView GET"""
        url = reverse(
            'projectroles:remote_projects',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_remote_project_batch_update(self):
        """Test RemoteProjectBatchUpdateView GET"""
        url = reverse(
            'projectroles:remote_projects_update',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestTargetSiteViews(
    RemoteSiteMixin, RemoteProjectMixin, ProjectPermissionTestBase
):
    """Tests for UI view permissions on target site"""

    def setUp(self):
        super().setUp()
        # Create site
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        # Create RemoteProject objects
        self.remote_category = self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )

    def test_get_project_detail(self):
        """Test ProjectDetailView GET"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_project_update(self):
        """Test ProjectUpdateView GET"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_create_top(self):
        """Test ProjectCreateView GET"""
        url = reverse('projectroles:create')
        self.assert_response(url, self.superuser, 200)
        self.assert_response(url, self.non_superusers, 302)

    # TODO: Add separate tests for local/remote creation
    # TODO: Remote creation should fail
    def test_get_project_create_local(self):
        """Test ProjectCreateView GET under local category"""
        # Make category local
        self.remote_category.delete()
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
        ]
        bad_users = [
            self.anonymous,
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_project_create_remote(self):
        """Test ProjectCreateView GET under local category"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.assert_response(url, self.all_users, 302)

    @override_settings(PROJECTROLES_TARGET_CREATE=False)
    def test_get_project_create_disallowed(self):
        """Test ProjectCreateView GET with creation disallowed"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_role_create(self):
        """Test RoleAssignmentCreateView GET"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_role_update(self):
        """Test RoleAssignmentUpdateView GET"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_role_update_delegate(self):
        """Test RoleAssignmentUpdateView GET for delegate role"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_role_delete(self):
        """Test RoleAssignmentDeleteView GET"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        # TODO: Superuser?
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_role_delete_delegate(self):
        """Test RoleAssignmentDeleteView GET for delegate role"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_project_invite_create(self):
        """Test ProjectInviteCreateView GET"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )

    def test_get_project_invite_list(self):
        """Test ProjectInviteListView GET"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_response(
            url, self.all_users, 302, redirect_anon=reverse('home')
        )


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestRevokedRemoteProjectViews(
    RemoteSiteMixin, RemoteProjectMixin, ProjectPermissionTestBase
):
    """
    Tests for UI view permissions with revoked remote project on target site.
    """

    def setUp(self):
        super().setUp()
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.remote_category = self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED'],
        )

    def test_get_project_detail(self):
        """Test ProjectDetailView GET"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_project_roles(self):
        """Test ProjectRoleView GET"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


class TestIPAllowing(IPAllowMixin, ProjectPermissionTestBase):
    """Tests for IP allow list permissions with ProjectDetailView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

    def test_get_http_x_forwarded_for_block_all(self):
        """Test GET with HTTP_X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.no_role_users, 302, header=header
            )

    def test_get_x_forwarded_for_block_all(self):
        """Test GET with X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.no_role_users, 302, header=header
            )

    def test_get_forwarded_block_all(self):
        """Test GET with FORWARDED and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.no_role_users, 302, header=header
            )

    def test_get_remote_addr_block_all(self):
        """Test GET with REMOTE_ADDR fwd and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.no_role_users, 302, header=header
            )

    def test_get_http_x_forwarded_for_allow_ip(self):
        """Test GET with HTTP_X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.user_no_roles, 200, header=header
            )
            self.assert_response(self.url, self.anonymous, 302, header=header)

    def test_get_x_forwarded_for_allow_ip(self):
        """Test GET with X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.user_no_roles, 200, header=header
            )
            self.assert_response(self.url, self.anonymous, 302, header=header)

    def test_get_forwarded_allow_ip(self):
        """Test GET with FORWARDED and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.user_no_roles, 200, header=header
            )
            self.assert_response(self.url, self.anonymous, 302, header=header)

    def test_get_remote_addr_allow_ip(self):
        """Test GET with REMOTE_ADDR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.user_no_roles, 200, header=header
            )
            self.assert_response(self.url, self.anonymous, 302, header=header)

    def test_get_remote_addr_allow_network(self):
        """Test GET with REMOTE_ADDR and allowed network"""
        self.setup_ip_allowing(['192.168.1.0/24'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.user_no_roles, 200, header=header
            )
            self.assert_response(self.url, self.anonymous, 302, header=header)

    def test_get_remote_addr_not_in_list_ip(self):
        """Test GET with REMOTE_ADDR and IP not in list"""
        self.setup_ip_allowing(['192.168.1.2'])
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.no_role_users, 302, header=header
            )

    def test_get_remote_addr_not_in_list_network(self):
        """Test GET with REMOTE_ADDR and network not in list"""
        self.setup_ip_allowing(['192.168.2.0/24'])
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response(
                self.url, self.no_role_users, 302, header=header
            )


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestIPAllowingTargetSite(
    IPAllowMixin, RemoteSiteMixin, RemoteProjectMixin, ProjectPermissionTestBase
):
    """Tests for IP allow list permissions on target site"""

    def setUp(self):
        super().setUp()
        # Create site
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        # Create RemoteProject objects
        self.remote_category = self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

    def test_get_http_x_forwarded_for_block_all(self):
        """Test GET with X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_x_forwarded_for_block_all(self):
        """Test GET with FORWARDED and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_forwarded_block_all(self):
        """Test GET with FORWARDED and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_remote_addr_block_all(self):
        """Test GET with REMOTE_ADDR fwd and block all"""
        self.setup_ip_allowing()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_http_x_forwarded_for_allow_ip(self):
        """Test GET with HTTP_X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_x_forwarded_for_allow_ip(self):
        """Test GET with X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_allowing_forwarded_allow_ip(self):
        """Test GET with FORWARDED and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_remote_addr_allow_ip(self):
        """Test GET with REMOTE_ADDR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_allowing_remote_addr_allow_network(self):
        """Test GET with REMOTE_ADDR and allowed network"""
        self.setup_ip_allowing(['192.168.1.0/24'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_remote_addr_not_in_list_ip(self):
        """Test GET with REMOTE_ADDR and IP not in list"""
        self.setup_ip_allowing(['192.168.1.2'])
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_remote_addr_not_in_list_network(self):
        """Test GET with REMOTE_ADDR and network not in list"""
        self.setup_ip_allowing(['192.168.2.0/24'])
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
