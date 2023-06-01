"""UI view permission tests for the projectroles app"""

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


class TestPermissionBase(TestPermissionMixin, TestCase):
    """
    Base class for permission tests for UI views.

    NOTE: To use with DRF API views, you need to use APITestCase
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

    NOTE: To use with DRF API views, you need to use APITestCase
    """

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


class TestBaseViews(TestProjectPermissionBase):
    """Tests for base UI views"""

    def test_home(self):
        """Test home view permissions"""
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
    def test_home_anon(self):
        """Test home view permissions with anonymous access"""
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

    def test_project_search(self):
        """Test search results permissions"""
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
    def test_project_search_anon(self):
        """Test search results permissions with anonymous access"""
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

    def test_project_search_advanced(self):
        """Test advanced search view permissions"""
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
    def test_project_search_advanced_anon(self):
        """Test advanced search permissions view with anonymous access"""
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

    def test_login(self):
        """Test login view permissions"""
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

    def test_logout(self):
        """Test logout view permissions"""
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

    def test_admin(self):
        """Test admin view permissions"""
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
    def test_admin_anon(self):
        """Test admin view permissions with anonymous access"""
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


class TestProjectViews(AppSettingMixin, TestProjectPermissionBase):
    """Permission tests for Project UI views"""

    def test_category_details(self):
        """Test category details permissions"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_category_details_anon(self):
        """Test permissions for category details with anonymous access"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_project_details(self):
        """Test project details permissions"""
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_details_anon(self):
        """Test project details permissions with anonymous access"""
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
        self.project.set_public()
        self.assert_response(url, bad_users, 200)

    def test_project_details_ip_http_x_forwarded_for_block_all(self):
        """Test IP allow list with HTTP_X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing([])
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
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302, header=header)

    def test_project_details_ip_x_forwarded_for_block_all(self):
        """Test IP allow list with X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing([])
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
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302, header=header)

    def test_project_details_ip_forwarded_block_all(self):
        """Test IP allow list with FORWARDED and block all"""
        self.setup_ip_allowing([])
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
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302, header=header)

    def test_project_details_ip_remote_addr_block_all(self):
        """Test IP allow list with REMOTE_ADDR fwd and block all"""
        self.setup_ip_allowing([])
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
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302, header=header)

    def test_project_details_ip_http_x_forwarded_for_allow_ip(self):
        """Test IP allow list with HTTP_X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, header=header)

    def test_project_details_ip_x_forwarded_for_allow_ip(self):
        """Test IP allow list with X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, header=header)

    def test_project_details_ip_forwarded_allow_ip(self):
        """Test IP allow list with FORWARDED and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, header=header)

    def test_project_details_ip_remote_addr_allow_ip(self):
        """Test IP allow list with REMOTE_ADDR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, header=header)

    def test_project_details_ip_remote_addr_allow_network(self):
        """Test IP allow list with REMOTE_ADDR and allowed network"""
        self.setup_ip_allowing(['192.168.1.0/24'])

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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, header=header)

    def test_project_details_ip_remote_addr_not_in_list_ip(self):
        """Test IP allow list with REMOTE_ADDR and IP not in list"""
        self.setup_ip_allowing(['192.168.1.2'])
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
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302, header=header)

    def test_project_details_ip_remote_addr_not_in_list_network(self):
        """Test IP allow list with REMOTE_ADDR and network not in list"""
        self.setup_ip_allowing(['192.168.2.0/24'])
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
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302, header=header)

    def test_create_top(self):
        """Test permissions for top level project creation"""
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_create_top_anon(self):
        """Test permissions for top level project creation with anonymous access"""
        url = reverse('projectroles:create')
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_create_sub(self):
        """Test permissions for subproject creation"""
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_create_sub_anon(self):
        """Test permissions for subproject creation with anonymous access"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_update(self):
        """Test project update permissions"""
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
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_update_anon(self):
        """Test project update permissions with anonymous access"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_update_category(self):
        """Test category update permissions"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_update_category_anon(self):
        """Test category update permissions with anonymous access"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_archive(self):
        """Test ProjectArchiveView permissions for project archiving"""
        url = reverse(
            'projectroles:archive', kwargs={'project': self.project.sodar_uuid}
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    def test_archive_category(self):
        """Test ProjectArchiveView permissions for category archiving"""
        url = reverse(
            'projectroles:archive', kwargs={'project': self.category.sodar_uuid}
        )
        bad_users_cat = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
        ]
        bad_users_other = [
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
            url,
            bad_users_cat,
            302,
            redirect_user=reverse(
                'projectroles:detail',
                kwargs={'project': self.category.sodar_uuid},
            ),
        )
        self.assert_response(
            url,
            bad_users_other,
            302,  # Non-category users get redirected to home
        )
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    def test_roles(self):
        """Test role list permissions"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_roles_anon(self):
        """Test role list permissions with anonymous access"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 200)

    def test_roles_category(self):
        """Test role list permissions under category"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.category.sodar_uuid}
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # public guest access is temporally disabled for categories
        with self.assertRaises(ValidationError):
            self.category.set_public()

    def test_role_create(self):
        """Test role create permissions"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
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
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_create_anon(self):
        """Test role create permissions with anonymous access"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_create_category(self):
        """Test role create permissions under category"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.category.sodar_uuid},
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # public guest access is temporarily disabled for categories
        with self.assertRaises(ValidationError):
            self.category.set_public()

    def test_role_create_archive(self):
        """Test permissions for role creation in archived project"""
        self.project.set_archive()
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
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
        self.assert_response(url, good_users, 200)  # Should be allowed
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    def test_role_update(self):
        """Test role update permissions"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
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
            self.user_guest,
            self.user_contributor,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_update_anon(self):
        """Test role update permissions with anonymous access"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_delete(self):
        """Test role delete permissions"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_delete_anon(self):
        """Test role delete permissions with anonymous access"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_update_owner(self):
        """Test permissions for owner role update (should fail)"""
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
    def test_role_update_owner_anon(self):
        """Test owner update permissions with anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_update_archive(self):
        """Test permissions for role updating for archived project"""
        self.project.set_archive()
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
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
        self.assert_response(url, good_users, 200)  # Should be allowed
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    def test_role_delete_owner(self):
        """Test owner delete permissions (should fail)"""
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
    def test_role_delete_owner_anon(self):
        """Test owner delete permissions with anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_update_delegate(self):
        """Test delegate update permissions"""
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

    def test_role_delete_delegate(self):
        """Test role delete permissions for delegate"""
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

    def test_role_owner_transfer(self):
        """Test owner update permissions"""
        url = reverse(
            'projectroles:role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
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

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_owner_transfer_anon(self):
        """Test owner update permissions with anonymous access (should fail)"""
        url = reverse(
            'projectroles:role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_invite_create(self):
        """Test invite create permissions"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_invite_create_anon(self):
        """Test invite create permissions with anonymous access (should fail)"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_invite_create_category(self):
        """Test invite create permissions under category"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.category.sodar_uuid},
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    def test_role_invite_list(self):
        """Test invite list permissions"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_invite_list_anon(self):
        """Test invite list permissions with anonymous access"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response(url, [self.user_no_roles, self.anonymous], 302)

    def test_role_invite_list_category(self):
        """Test invite list permissions under category"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.category.sodar_uuid}
        )
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
        # public guest access is temporally disabled for categories
        with self.assertRaises(ValidationError):
            self.category.set_public()

    def test_role_invite_resend(self):
        """Test invite resend permissions"""
        # Init invite
        invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )
        url = reverse(
            'projectroles:invite_resend',
            kwargs={'projectinvite': invite.sodar_uuid},
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
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user=reverse(
                'projectroles:invites',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)

    def test_role_invite_revoke(self):
        """Test invite revoke permissions"""
        # Init invite
        invite = self.make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )

        url = reverse(
            'projectroles:invite_revoke',
            kwargs={'projectinvite': invite.sodar_uuid},
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
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 302)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestTargetProjectViews(
    AppSettingMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestProjectPermissionBase,
):
    """Tests for Project updating views on a TARGET site"""

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

    def test_project_details(self):
        """Test project details permissions"""
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

    def test_project_details_ip_http_x_forwarded_for_block_all(self):
        """Test target site IP allow list with X_FORWARDED_FOR and block all"""
        self.setup_ip_allowing([])
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
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_x_forwarded_for_block_all(self):
        """Test target site IP allow list with FORWARDED and block all"""
        self.setup_ip_allowing([])
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
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_forwarded_block_all(self):
        """Test target site IP allow list with FORWARDED and block all"""
        self.setup_ip_allowing([])
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
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_remote_addr_block_all(self):
        """Test target site IP allow list with REMOTE_ADDR fwd and block all"""
        self.setup_ip_allowing([])
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
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_http_x_forwarded_for_allow_ip(self):
        """Test target site IP allow list with HTTP_X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'HTTP_X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_x_forwarded_for_allow_ip(self):
        """Test target site IP allow list with X_FORWARDED_FOR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'X_FORWARDED_FOR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_allowing_forwarded_allow_ip(self):
        """Test target site IP allow list with FORWARDED and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'FORWARDED': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_remote_addr_allow_ip(self):
        """Test target site IP allow list with REMOTE_ADDR and allowed IP"""
        self.setup_ip_allowing(['192.168.1.1'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_allowing_remote_addr_allow_network(self):
        """Test target site IP allow list with REMOTE_ADDR and allowed network"""
        self.setup_ip_allowing(['192.168.1.0/24'])
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
        bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_remote_addr_not_in_list_ip(self):
        """Test target site IP allow list with REMOTE_ADDR and IP not in list"""
        self.setup_ip_allowing(['192.168.1.2'])
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
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_project_details_ip_remote_addr_not_in_list_network(self):
        """Test target site IP allow list with REMOTE_ADDR and network not in list"""
        self.setup_ip_allowing(['192.168.2.0/24'])
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
            self.anonymous,
        ]
        header = {'REMOTE_ADDR': '192.168.1.1'}
        self.assert_response(url, good_users, 200, header=header)
        self.assert_response(url, bad_users, 302, header=header)

    def test_update(self):
        """Test project update permissions as target"""
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

    def test_create_top_allowed(self):
        """Test top project create permissions as target"""
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
    def test_create_sub_local(self):
        """Test project create permissions as target under local category"""
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

    def test_create_sub_remote(self):
        """Test project create permissions as target under local category"""
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
    def test_create_sub_disallowed(self):
        """Test project create permissions with creation disallowed as target"""
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

    def test_role_create(self):
        """Test role create permissions as target"""
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

    def test_role_update(self):
        """Test role update permissions as target"""
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

    def test_role_delete(self):
        """Test role delete permissions as target"""
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

    def test_role_update_delegate(self):
        """Test delegate role update permissions as target"""
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

    def test_role_delete_delegate(self):
        """Test role delete permissions for delegate as target"""
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

    def test_role_invite_create(self):
        """Test invite create permissions as target"""
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

    def test_role_invite_list(self):
        """Test invite list permissions as target"""
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
class TestRevokedRemoteProject(
    RemoteSiteMixin, RemoteProjectMixin, TestProjectPermissionBase
):
    """Tests for views for a revoked project on a TARGET site"""

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
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED'],
        )

    def test_project_details(self):
        """Test REVOKED project details permissions as target"""
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

    def test_role_list(self):
        """Test REVOKED project role list permissions as target"""
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


class TestRemoteSiteApp(RemoteSiteMixin, TestPermissionBase):
    """Tests for remote site management views"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()
        self.regular_user = self.make_user('regular_user')
        # No user
        self.anonymous = None
        # Create site
        self.site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

    def test_site_list(self):
        """Test remote site list view permissions"""
        url = reverse('projectroles:remote_sites')
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_site_create(self):
        """Test remote site create view permissions"""
        url = reverse('projectroles:remote_site_create')
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_site_update(self):
        """Test remote site update view permissions"""
        url = reverse(
            'projectroles:remote_site_update',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_site_delete(self):
        """Test remote site delete view permissions"""
        url = reverse(
            'projectroles:remote_site_delete',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_project_list(self):
        """Test remote project list view permissions"""
        url = reverse(
            'projectroles:remote_projects',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_project_update(self):
        """Test remote project update view permissions"""
        url = reverse(
            'projectroles:remote_projects_update',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.regular_user, self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
