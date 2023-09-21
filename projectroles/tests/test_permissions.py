"""Tests for UI view permissions in the projectroles app"""

from urllib.parse import urlencode, quote

from django.test import override_settings
from django.urls import reverse
from django.core.exceptions import ValidationError

from test_plus.test import TestCase

from projectroles.models import SODAR_CONSTANTS
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


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']

# Local constants
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_SECRET = build_secret()


class TestPermissionMixin:
    """Helper class for permission tests"""

    def send_request(self, url, method, req_kwargs):
        req_method = getattr(self.client, method.lower(), None)
        if not req_method:
            raise ValueError('Invalid method "{}"'.format(method))
        return req_method(url, **req_kwargs)

    def assert_response(
        self,
        url,
        users,
        status_code,
        redirect_user=None,
        redirect_anon=None,
        method='GET',
        data=None,
        header=None,
        cleanup_method=None,
        req_kwargs=None,
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

            msg = 'user={}'.format(user)
            self.assertEqual(response.status_code, status_code, msg=msg)
            if status_code == 302:
                self.assertEqual(response.url, re_url, msg=msg)
            if cleanup_method:
                cleanup_method()


class IPAllowMixin(AppSettingMixin):
    """Mixin for IP allowing test helpers"""

    def setup_ip_allowing(self, ip_list):
        # Init IP restrict setting
        self.make_setting(
            app_name='projectroles',
            name='ip_restrict',
            setting_type='BOOLEAN',
            value=True,
            project=self.project,
        )
        # Init IP allowlist setting
        self.make_setting(
            app_name='projectroles',
            name='ip_allowlist',
            setting_type='JSON',
            value=None,
            value_json=ip_list,
            project=self.project,
        )


class TestPermissionBase(TestPermissionMixin, TestCase):
    """
    Base class for permission tests for UI views.

    NOTE: For REST API views, you need to use APITestCase
    """


class TestProjectPermissionBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    TestPermissionBase,
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
        self.user_guest_cat = self.make_user('user_guest_cat')
        self.user_finder_cat = self.make_user('user_finder_cat')
        self.user_owner = self.make_user('user_owner')
        self.user_delegate = self.make_user('user_delegate')
        self.user_contributor = self.make_user('user_contributor')
        self.user_guest = self.make_user('user_guest')
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


class TestSiteAppPermissionBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    TestPermissionBase,
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


class TestGeneralViews(TestProjectPermissionBase):
    """Tests for general non-project UI view permissions"""

    def test_get_home(self):
        """Test HomeView GET"""
        url = reverse('home')
        good_users = [
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
            self.user_no_roles,
        ]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_home_anon(self):
        """Test HomeView GET with anonymous access"""
        url = reverse('home')
        good_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)

    def test_get_search(self):
        """Test ProjectSearchResultsView GET"""
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        good_users = [
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
            self.user_no_roles,
        ]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(reverse('home'), bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_search_anon(self):
        """Test ProjectSearchResultsView GET with anonymous access"""
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        good_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)

    def test_get_search_advanced(self):
        """Test ProjectAdvancedSearchView GET"""
        url = reverse('projectroles:search_advanced')
        good_users = [
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
            self.user_no_roles,
        ]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(reverse('home'), bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_search_advanced_anon(self):
        """Test ProjectAdvancedSearchView GET with anonymous access"""
        url = reverse('projectroles:search_advanced')
        good_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)

    def test_get_login(self):
        """Test LoginView GET"""
        url = reverse('login')
        good_users = [
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
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)

    def test_get_logout(self):
        """Test logout view GET"""
        url = reverse('logout')
        good_users = [
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
            self.user_no_roles,
        ]
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user='/login/',
            redirect_anon='/login/',
        )

    def test_get_admin(self):
        """Test admin view GET"""
        url = '/admin/'
        good_users = [self.superuser]
        bad_users = [
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
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(
            url,
            bad_users,
            302,
            redirect_user='/admin/login/?next=/admin/',
            redirect_anon='/admin/login/?next=/admin/',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_admin_anon(self):
        """Test admin view GET with anonymous access"""
        url = '/admin/'
        good_users = [self.superuser]
        bad_users = [
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
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(
            url,
            bad_users,
            302,
            redirect_user='/admin/login/?next=/admin/',
            redirect_anon='/admin/login/?next=/admin/',
        )


class TestProjectDetailView(TestProjectPermissionBase):
    """Tests for ProjectDetailView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectDetailView GET"""
        good_users = [
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        good_users = [
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        good_users = [
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
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
        bad_users = [self.user_no_roles, self.anonymous]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        good_users = [
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
        bad_users = [self.user_no_roles, self.anonymous]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)


class TestProjectCreateView(TestProjectPermissionBase):
    """Tests for ProjectCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url_top = reverse('projectroles:create')
        self.url_sub = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )

    def test_get_top(self):
        """Test ProjectCreateView GET for top level creation"""
        good_users = [self.superuser]
        bad_users = [
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
            self.anonymous,
        ]
        self.assert_response(self.url_top, good_users, 200)
        self.assert_response(self.url_top, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_top, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_top_anon(self):
        """Test GET for top level creation with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url_top, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_sub(self):
        """Test GET for subproject creation"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
        ]
        bad_users = [
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_sub, good_users, 200)
        self.assert_response(self.url_sub, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_sub, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_sub_anon(self):
        """Test GET for subproject creation with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url_sub, [self.user_no_roles, self.anonymous], 302
        )


class TestProjectUpdateView(TestProjectPermissionBase):
    """Tests for ProjectUpdateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectUpdateView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url_cat, [self.user_no_roles, self.anonymous], 302
        )


class TestProjectArchiveView(TestProjectPermissionBase):
    """Tests for ProjectArchiveView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:archive', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:archive', kwargs={'project': self.category.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectArchiveView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test GET with category"""
        bad_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users_non_cat = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(
            self.url_cat,
            bad_users_cat,
            302,
            redirect_user=reverse(
                'projectroles:detail',
                kwargs={'project': self.category.sodar_uuid},
            ),
        )
        self.assert_response(
            self.url_cat,
            bad_users_non_cat,
            302,  # Non-category users get redirected to home
        )
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 302)


class TestProjectRoleView(TestProjectPermissionBase):
    """Tests for ProjectRoleView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:roles', kwargs={'project': self.category.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectRoleView GET"""
        good_users = [
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 200
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        good_users = [
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        # Public guest access is disabled for categories
        with self.assertRaises(ValidationError):
            self.category.set_public()


class TestRoleAssignmentCreateView(TestProjectPermissionBase):
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

    def test_get(self):
        """Test RoleAssignmentCreateView GET"""
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
            self.user_finder_cat,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        # Public guest access is disabled for categories
        with self.assertRaises(ValidationError):
            self.category.set_public()


class TestRoleAssignmentUpdateView(TestProjectPermissionBase):
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

    def test_get(self):
        """Test RoleAssignmentUpdateView GET"""
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
            self.user_finder_cat,
            self.user_guest,
            self.user_contributor,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_guest,
            self.user_contributor,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_contributor,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url_cat, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_owner(self):
        """Test GET with owner role (should fail)"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_owner_anon(self):
        """Test GET with owner role with anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)


class TestRoleAssignmentDeleteView(TestProjectPermissionBase):
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

    def test_get(self):
        """Test RoleAssignmentDeleteView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test RoleAssignmentDeleteView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
            self.user_owner,
            self.user_delegate,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url_cat, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_owner(self):
        """Test GET with owner role (should fail)"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_owner_anon(self):
        """Test GET with owner role and anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

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
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)


class TestRoleAssignmentOwnerTransferView(TestProjectPermissionBase):
    """Tests for RoleAssignmentOwnerTransferView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test RoleAssignmentOwnerTransferView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
        ]
        bad_users = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access (should fail)"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
        ]
        bad_users = [
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)


class TestProjectInviteView(TestProjectPermissionBase):
    """Tests for ProjectInviteView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.url_cat = reverse(
            'projectroles:invites', kwargs={'project': self.category.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectInviteView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        # public guest access is temporally disabled for categories
        with self.assertRaises(ValidationError):
            self.category.set_public()


class TestProjectInviteCreateView(TestProjectPermissionBase):
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

    def test_get(self):
        """Test ProjectInviteCreateView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    def test_get_category(self):
        """Test GET with category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url_cat, good_users, 200)
        self.assert_response(self.url_cat, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 302)


class TestProjectInviteResendView(TestProjectPermissionBase):
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

    def test_get(self):
        """Test ProjectInviteResendView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(
            self.url,
            good_users,
            302,
            redirect_user=reverse(
                'projectroles:invites',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(
            self.url,
            good_users,
            302,
            redirect_user=reverse(
                'projectroles:invites',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)


class TestProjectInviteRevokeView(TestProjectPermissionBase):
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

    def test_get(self):
        """Test ProjectInviteRevokeView GET"""
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 302
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302)


class TestRemoteSiteViews(RemoteSiteMixin, TestSiteAppPermissionBase):
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

    def test_get_remmote_site_update(self):
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
    RemoteSiteMixin, RemoteProjectMixin, TestProjectPermissionBase
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
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_create_top(self):
        """Test ProjectCreateView GET"""
        url = reverse('projectroles:create')
        good_users = [self.superuser]
        bad_users = [
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
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

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
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_get_project_create_remote(self):
        """Test ProjectCreateView GET under local category"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_TARGET_CREATE=False)
    def test_get_project_create_disallowed(self):
        """Test ProjectCreateView GET with creation disallowed"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)

    def test_get_role_create(self):
        """Test RoleAssignmentCreateView GET"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_role_update(self):
        """Test RoleAssignmentUpdateView GET"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_role_update_delegate(self):
        """Test RoleAssignmentUpdateView GET for delegate role"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_role_delete(self):
        """Test RoleAssignmentDeleteView GET"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        bad_users = [
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
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_role_delete_delegate(self):
        """Test RoleAssignmentDeleteView GET for delegate role"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
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
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_project_invite_create(self):
        """Test ProjectInviteCreateView GET"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))

    def test_get_project_invite_list(self):
        """Test ProjectInviteListView GET"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        bad_users = [
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
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302, redirect_anon=reverse('home'))


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestRevokedRemoteProjectViews(
    RemoteSiteMixin, RemoteProjectMixin, TestProjectPermissionBase
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


class TestIPAllowing(IPAllowMixin, TestProjectPermissionBase):
    """Tests for IP allow list permissions with ProjectDetailView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

    def test_get_http_x_forwarded_for_block_all(self):
        """Test GET with HTTP_X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302, header=header)

    def test_get_x_forwarded_for_block_all(self):
        """Test GET with X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302, header=header)

    def test_get_forwarded_block_all(self):
        """Test GET with FORWARDED and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302, header=header)

    def test_get_remote_addr_block_all(self):
        """Test GET with REMOTE_ADDR fwd and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302, header=header)

    def test_get_http_x_forwarded_for_allow_ip(self):
        """Test GET with HTTP_X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200, header=header)

    def test_get_x_forwarded_for_allow_ip(self):
        """Test GET with X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200, header=header)

    def test_get_forwarded_allow_ip(self):
        """Test GET with FORWARDED and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200, header=header)

    def test_get_remote_addr_allow_ip(self):
        """Test GET with REMOTE_ADDR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200, header=header)

    def test_get_remote_addr_allow_network(self):
        """Test GET with REMOTE_ADDR and allowed network"""
        self.setup_ip_allowing(['192.168.1.0/24'])
        good_users = [
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200, header=header)

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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302, header=header)

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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 302, header=header)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestIPAllowingTargetSite(
    IPAllowMixin, RemoteSiteMixin, RemoteProjectMixin, TestProjectPermissionBase
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
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_x_forwarded_for_block_all(self):
        """Test GET with FORWARDED and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_forwarded_block_all(self):
        """Test GET with FORWARDED and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)

    def test_get_remote_addr_block_all(self):
        """Test GET with REMOTE_ADDR fwd and block all"""
        self.setup_ip_allowing([])
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
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
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
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
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(self.url, good_users, 200, header=header)
        self.assert_response(self.url, bad_users, 302, header=header)
