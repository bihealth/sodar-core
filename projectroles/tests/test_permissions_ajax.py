"""Ajax API view permission tests for the projectroles app"""

from django.test import override_settings
from django.urls import reverse

from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import RemoteSiteMixin, RemoteProjectMixin
from projectroles.tests.test_permissions import ProjectPermissionTestBase

# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']


class TestProjectListAjaxViews(ProjectPermissionTestBase):
    """Tests for project list Ajax view permissions"""

    def test_get_project_list(self):
        """Test ProjectListAjaxView GET"""
        url = reverse('projectroles:ajax_project_list')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_project_list_anon(self):
        """Test ProjectListAjaxView GET with anonymous access"""
        url = reverse('projectroles:ajax_project_list')
        self.assert_response(url, self.anonymous, 200)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 200)

    def test_get_project_list_read_only(self):
        """Test ProjectListAjaxView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('projectroles:ajax_project_list')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    def test_get_project_list_column(self):
        """Test ProjectListColumnAjaxView GET"""
        url = reverse('projectroles:ajax_project_list_columns')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
        self.assert_response(
            url,
            self.auth_users,
            200,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.project.set_public()
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_project_list_column_anon(self):
        """Test ProjectListColumnAjaxView GET with anonymous access"""
        url = reverse('projectroles:ajax_project_list_columns')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
        self.project.set_public()
        self.assert_response(
            url,
            self.anonymous,
            200,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )

    def test_get_project_list_column_read_only(self):
        """Test ProjectListColumnAjaxView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('projectroles:ajax_project_list_columns')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
        self.assert_response(
            url,
            self.auth_users,
            200,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )

    def test_get_project_list_role(self):
        """Test ProjectListRoleAjaxView GET"""
        url = reverse('projectroles:ajax_project_list_roles')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
        self.assert_response(
            url,
            self.auth_users,
            200,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.project.set_public()
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_project_list_role_anon(self):
        """Test ProjectListRoleAjaxView GET with anonymous access"""
        url = reverse('projectroles:ajax_project_list_roles')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
        self.project.set_public()
        self.assert_response(
            url,
            self.anonymous,
            200,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )

    def test_get_project_list_role_read_only(self):
        """Test ProjectListRoleAjaxView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('projectroles:ajax_project_list_roles')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
        self.assert_response(
            url,
            self.auth_users,
            200,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )
        self.project.set_public()
        self.assert_response(
            url,
            self.anonymous,
            403,
            method='POST',
            data=data,
            req_kwargs=req_kwargs,
        )


class TestProjectStarringAjaxView(ProjectPermissionTestBase):
    """Tests for ProjectStarringAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_post(self):
        """Test ProjectStarringAjaxView POST"""
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
        self.assert_response(self.url, good_users, 200, method='POST')
        self.assert_response(self.url, bad_users, 403, method='POST')
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 401, method='POST')

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.superuser, 200, method='POST')
        self.assert_response(self.url, self.non_superusers, 403, method='POST')

    def test_post_category(self):
        """Test POST with category"""
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
        self.assert_response(self.url_cat, good_users, 200, method='POST')
        self.assert_response(self.url_cat, bad_users, 403, method='POST')
        self.project.set_public()
        self.assert_response(
            self.url_cat, self.user_no_roles, 200, method='POST'
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_category_anon(self):
        """Test POST with category and anonymous access"""
        self.project.set_public()
        self.assert_response(self.url_cat, self.anonymous, 401, method='POST')

    def test_post_category_read_only(self):
        """Test POST with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.superuser, 200, method='POST')
        self.assert_response(
            self.url_cat, self.non_superusers, 403, method='POST'
        )


class TestRemoteProjectAccessAjaxView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectPermissionTestBase
):
    """Tests for RemoteProjectAccessAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.remote_site = self.make_site(
            name='RemoteSite',
            url='https://remote.site',
            mode=SITE_MODE_TARGET,
        )
        self.remote_project = self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=self.remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        self.url = reverse(
            'projectroles:ajax_remote_access',
            kwargs={'project': self.project.sodar_uuid},
        ) + '?rp={}'.format(self.remote_project.sodar_uuid)
        self.good_users = [
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
        self.bad_users = [
            self.user_finder_cat,
            self.user_no_roles,
            self.anonymous,
        ]

    def test_get(self):
        """Test RemoteProjectAccessAjaxView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)


class TestSidebarContentAjaxView(ProjectPermissionTestBase):
    """Tests for SidebarContentAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:ajax_sidebar',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:ajax_sidebar',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.good_users = [
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
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        self.bad_users_cat = [self.user_no_roles, self.anonymous]

    def test_get(self):
        """Test SidebarContentAjaxView GET"""
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.good_users, 200)
        self.assert_response(self.url, self.bad_users, 403)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 403)
        self.project.set_public()
        self.assert_response(self.url_cat, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_anon(self):
        """Test GET with category and anonymous access"""
        self.project.set_public()
        self.assert_response(self.url_cat, self.anonymous, 200)

    def test_get_category_read_only(self):
        """Test GET with category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url_cat, self.good_users_cat, 200)
        self.assert_response(self.url_cat, self.bad_users_cat, 403)


class TestSiteReadOnlySettingAjaxView(ProjectPermissionTestBase):
    """Tests for SiteReadOnlySettingAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:ajax_settings_site_read_only')

    def test_get(self):
        """Test SiteReadOnlySettingAjaxView GET"""
        self.assert_response(self.url, self.auth_users, 200)
        self.assert_response(self.url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response(self.url, self.anonymous, 200)


class TestUserDropdownContentAjaxView(ProjectPermissionTestBase):
    """Tests for UserDropdownContentAjaxView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:ajax_user_dropdown')

    def test_get(self):
        """Test UserDropdownContentAjaxView GET"""
        self.assert_response(self.url, self.auth_users, 200)
        self.assert_response(self.url, self.anonymous, 403)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response(self.url, self.auth_users, 200)
        self.assert_response(self.url, self.anonymous, 403)


class TestUserAjaxViews(ProjectPermissionTestBase):
    """Tests for user Ajax view permissions"""

    def test_get_current_user(self):
        """Test CurrentUserRetrieveAjaxView GET"""
        url = reverse('projectroles:ajax_user_current')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 403)

    def test_get_current_user_read_only(self):
        """Test CurrentUserRetrieveAjaxView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('projectroles:ajax_user_current')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_autocomplete_ajax(self):
        """Test UserAutocompleteAjaxView GET"""
        url = reverse('projectroles:ajax_autocomplete_user')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_get_autocomplete_ajax_read_only(self):
        """Test UserAutocompleteAjaxView GET with site read-only mode"""
        self.set_site_read_only()
        url = reverse('projectroles:ajax_autocomplete_user')
        self.assert_response(url, self.auth_users, 200)
        self.assert_response(url, self.anonymous, 403)
