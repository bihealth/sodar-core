"""Tests for UI view permissions in the projectroles app"""

from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse

from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.utils import build_secret
from projectroles.tests.base import (
    PermissionTestMixin as MovedPermissionTestMixin,
    IPAllowMixin as MovedIPAllowMixin,
    PermissionTestBase as MovedPermissionTestBase,
    ProjectPermissionTestBase as MovedProjectPermissionTestBase,
    SiteAppPermissionTestBase as MovedSiteAppPermissionTestBase,
    TEST_BASE_CLASS_DEPRECATE_MSG,
)
from projectroles.tests.test_models import RemoteSiteMixin, RemoteProjectMixin


app_settings = AppSettingAPI()
User = get_user_model()


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


# TODO: Remove in v1.4 (see #1830)
class PermissionTestMixin(MovedPermissionTestMixin):
    """
    Helper class for permission tests.

    DEPRECATED: To be removed in v1.4. Use
    projectroles.tests.base.PermissionTestMixin instead.
    """


# TODO: Remove in v1.4 (see #1830)
class IPAllowMixin(MovedIPAllowMixin):
    """
    Mixin for IP allowing test helpers.

    DEPRECATED: To be removed in v1.4. Use
    projectroles.tests.base.IPAllowMixin instead.
    """


# TODO: Remove in v1.4 (see #1830)
class PermissionTestBase(MovedPermissionTestBase):
    """
    Base class for permission tests for UI views.

    NOTE: For REST API views, you need to use APITestCase.

    DEPRECATED: To be removed in v1.4. Use
    projectroles.tests.base.PermissionTestBase instead.
    """


# TODO: Remove in v1.4 (see #1830)
class ProjectPermissionTestBase(MovedProjectPermissionTestBase):
    """
    Base class for testing project permissions.

    NOTE: For REST API views, you need to use APITestCase.

    DEPRECATED: To be removed in v1.4. Use
    projectroles.tests.base.ProjectPermissionTestBase instead.
    """

    def setUp(self):
        super().setUp()
        c = 'ProjectPermissionTestBase'
        print(TEST_BASE_CLASS_DEPRECATE_MSG.format(old=c, new=c))


# TODO: Remove in v1.4 (see #1830)
class SiteAppPermissionTestBase(MovedSiteAppPermissionTestBase):
    """
    Base class for testing site app permissions.

    DEPRECATED: To be removed in v1.4. Use
    projectroles.tests.base.SiteAppPermissionTestBase instead.
    """

    def setUp(self):
        super().setUp()
        c = 'SiteAppPermissionTestBase'
        print(TEST_BASE_CLASS_DEPRECATE_MSG.format(old=c, new=c))


class TestGeneralViews(MovedProjectPermissionTestBase):
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

    def test_post_logout(self):
        """Test logout view POST"""
        url = reverse('logout')
        self.assert_response(
            url,
            self.auth_users,
            302,
            method='POST',
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


class TestProjectDetailView(MovedProjectPermissionTestBase):
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


class TestProjectCreateView(MovedProjectPermissionTestBase):
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


class TestProjectUpdateView(MovedProjectPermissionTestBase):
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


class TestProjectArchiveView(MovedProjectPermissionTestBase):
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
    RemoteSiteMixin, RemoteProjectMixin, MovedProjectPermissionTestBase
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


class TestProjectRoleView(MovedProjectPermissionTestBase):
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


class TestRoleAssignmentCreateView(MovedProjectPermissionTestBase):
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


class TestRoleAssignmentUpdateView(MovedProjectPermissionTestBase):
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


class TestRoleAssignmentDeleteView(MovedProjectPermissionTestBase):
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


class TestRoleAssignmentOwnDeleteView(MovedProjectPermissionTestBase):
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


class TestRoleAssignmentOwnerTransferView(MovedProjectPermissionTestBase):
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


class TestProjectInviteView(MovedProjectPermissionTestBase):
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


class TestProjectInviteCreateView(MovedProjectPermissionTestBase):
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


class TestProjectInviteResendView(MovedProjectPermissionTestBase):
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


class TestProjectInviteRevokeView(MovedProjectPermissionTestBase):
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


class TestSiteAppSettingsFormView(MovedProjectPermissionTestBase):
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


class TestRemoteSiteViews(RemoteSiteMixin, MovedSiteAppPermissionTestBase):
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
    RemoteSiteMixin, RemoteProjectMixin, MovedProjectPermissionTestBase
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
    RemoteSiteMixin, RemoteProjectMixin, MovedProjectPermissionTestBase
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


class TestIPAllowing(IPAllowMixin, MovedProjectPermissionTestBase):
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
    IPAllowMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    MovedProjectPermissionTestBase,
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
