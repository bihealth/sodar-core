"""Ajax API view permission tests for the projectroles app"""

from django.test import override_settings
from django.urls import reverse

from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_permissions import TestProjectPermissionBase


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestProjectViews(TestProjectPermissionBase):
    """Permission tests for Project Ajax views"""

    def test_project_list_ajax(self):
        """Test ProjectListAjaxView permissions"""
        url = reverse('projectroles:ajax_project_list')
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
        self.assert_response(url, good_users, 200)
        self.assert_response(url, self.anonymous, 403)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_list_ajax_anon(self):
        """Test ProjectListAjaxView permissions with anonymous access"""
        url = reverse('projectroles:ajax_project_list')
        self.assert_response(url, self.anonymous, 200)
        self.project.set_public()
        self.assert_response(url, self.anonymous, 200)

    def test_project_list_column_ajax(self):
        """Test ProjectListColumnAjaxView permissions"""
        url = reverse('projectroles:ajax_project_list_columns')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
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
    def test_project_list_column_ajax_anon(self):
        """Test ProjectListColumnAjaxView permissions with anonymous access"""
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

    def test_project_list_role_ajax(self):
        """Test ProjectListRoleAjaxView permissions"""
        url = reverse('projectroles:ajax_project_list_roles')
        data = {'projects': [str(self.project.sodar_uuid)]}
        req_kwargs = {'content_type': 'application/json'}
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
    def test_project_list_role_ajax_anon(self):
        """Test ProjectListRoleAjaxView permissions with anonymous access"""
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

    def test_starring_ajax(self):
        """Test ProjectStarringAjaxView permissions"""
        url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.project.sodar_uuid},
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
        self.assert_response(url, good_users, 200, method='POST')
        self.assert_response(url, bad_users, 403, method='POST')
        # Test public project
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_starring_ajax_anon(self):
        """Test ProjectStarringAjaxView permissions with anonymous access"""
        url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 401, method='POST')

    def test_starring_ajax_category(self):
        """Test ProjectStarringAjaxView permissions with category"""
        url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.category.sodar_uuid},
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
        self.assert_response(url, good_users, 200, method='POST')
        self.assert_response(url, bad_users, 403, method='POST')
        # Test public project
        self.project.set_public()
        self.assert_response(url, self.user_no_roles, 200, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_starring_ajax_category_anon(self):
        """Test ProjectStarringAjaxView permissions with category and anon access"""
        url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.category.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response(url, self.anonymous, 401, method='POST')

    def test_current_user(self):
        """Test CurrentUserRetrieveAjaxView access"""
        url = reverse('projectroles:ajax_user_current')
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
        self.assert_response(url, bad_users, 403)

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_user_autocomplete_ajax(self):
        """Test UserAutocompleteAjaxView access"""
        url = reverse('projectroles:ajax_autocomplete_user')
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
        self.assert_response(url, bad_users, 403)
