"""REST API view permission tests for the projectroles app"""

import uuid

from typing import Optional, Union

from django.http import HttpResponse
from django.test import override_settings
from django.urls import reverse

from projectroles.models import (
    Project,
    RoleAssignment,
    ProjectInvite,
    SODARUser,
    SODAR_CONSTANTS,
)
from projectroles.tests.test_models import RemoteSiteMixin, RemoteProjectMixin
from projectroles.tests.test_permissions import ProjectPermissionTestBase
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.utils import build_secret
from projectroles.views_api import (
    PROJECTROLES_API_MEDIA_TYPE,
    PROJECTROLES_API_DEFAULT_VERSION,
)

from rest_framework.test import APITestCase


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']

# Local constants
APP_NAME_EX = 'example_project_app'
NEW_PROJECT_TITLE = 'New Project'
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_SECRET = build_secret()


# Base Classes and Mixins ------------------------------------------------------


class SODARAPIPermissionTestMixin(SODARAPIViewTestMixin):
    """Mixin for permission testing with knox auth"""

    def assert_response_api(
        self,
        url: str,
        users: Union[list, tuple, SODARUser],
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


class ProjectrolesAPIPermissionTestBase(ProjectAPIPermissionTestBase):
    """Base class for testing projectroles app REST API view permissions"""

    media_type = PROJECTROLES_API_MEDIA_TYPE
    api_version = PROJECTROLES_API_DEFAULT_VERSION


# Tests ------------------------------------------------------------------------


class TestProjectListAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectListAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_project_list')

    def test_get(self):
        """Test ProjectListAPIView GET"""
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.auth_users, 200, knox=True)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestProjectRetrieveAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.category.sodar_uuid},
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
        ]
        self.bad_users = [self.user_finder_cat, self.user_no_roles]

    def test_get(self):
        """Test ProjectRetrieveAPIView GET"""
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.assert_response_api(self.url, self.bad_users, 403, knox=True)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 200)
            self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.no_role_users, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 200)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_category(self):
        """Test GET with category"""
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_category_public_stats(self):
        """Test GET with category and public stats"""
        self.set_category_public_stats(self.category)
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_category_public_stats_anon(self):
        """Test GET with category and public stats and anonymous access"""
        self.set_category_public_stats(self.category)
        self.assert_response_api(self.url, self.user_no_roles, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestProjectCreateAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectCreateAPIView permissions"""

    def _cleanup(self):
        Project.objects.filter(title=NEW_PROJECT_TITLE).delete()

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_project_create')
        self.post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'],
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
            'public_access': None,
        }
        self.post_data_parent = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
            'public_access': None,
        }

    def test_post_top(self):
        """Test ProjectCreateAPIView POST on top level"""
        good_users = self.superuser
        bad_users = self.auth_non_superusers
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_top_anon(self):
        """Test POST with top level and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_top_read_only(self):
        """Test POST on top level with site read-only mode"""
        self.set_site_read_only()
        good_users = [self.superuser]
        bad_users = self.auth_non_superusers
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_parent(self):
        """Test POST with parent category"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
        ]
        bad_users = [
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            data=self.post_data_parent,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='POST', data=self.post_data_parent
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='POST',
            data=self.post_data_parent,
        )
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            data=self.post_data_parent,
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='POST',
            data=self.post_data_parent,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data_parent,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_parent_anon(self):
        """Test POST with parent category and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data_parent,
            )

    def test_post_parent_read_only(self):
        """Test POST with parent category and site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data_parent,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data_parent,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='POST',
            data=self.post_data_parent,
        )


class TestProjectUpdateAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectUpdateAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.put_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
            'public_access': None,
        }
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
        ]

    def test_put(self):
        """Test ProjectUpdateAPIView PUT"""
        self.assert_response_api(
            self.url, self.good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='PUT',
                data=self.put_data,
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='PUT', data=self.put_data
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.anonymous, 401, method='PUT', data=self.put_data
            )

    def test_put_archive(self):
        """Test PUT with archived project"""
        self.assert_response_api(
            self.url, self.good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='PUT',
                data=self.put_data,
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='PUT', data=self.put_data
            )

    def test_put_block(self):
        """Test PUT with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url, self.superuser, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    def test_put_read_only(self):
        """Test PUT with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.superuser, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )


class TestProjectDestroyAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIPermissionTestBase
):
    """Tests for ProjectDestroyAPIView permissions"""

    def _cleanup(self, make_project: bool = True):
        if not Project.objects.filter(sodar_uuid=self.cat_uuid).first():
            self.category = self.make_project(
                title='TestCategory',
                type=PROJECT_TYPE_CATEGORY,
                parent=None,
                sodar_uuid=self.cat_uuid,
            )
            self.make_assignment(
                self.category, self.user_owner_cat, self.role_owner
            )
            self.make_assignment(
                self.category, self.user_delegate_cat, self.role_delegate
            )
            self.make_assignment(
                self.category, self.user_contributor_cat, self.role_contributor
            )
            self.make_assignment(
                self.category, self.user_guest_cat, self.role_guest
            )
            self.make_assignment(
                self.category, self.user_finder_cat, self.role_finder
            )
        if (
            make_project
            and not Project.objects.filter(sodar_uuid=self.project_uuid).first()
        ):
            self.project = self.make_project(
                title='TestProject',
                type=PROJECT_TYPE_PROJECT,
                parent=self.category,
                sodar_uuid=self.project_uuid,
            )
            self.make_assignment(self.project, self.user_owner, self.role_owner)
            self.make_assignment(
                self.project, self.user_delegate, self.role_delegate
            )
            self.make_assignment(
                self.project, self.user_contributor, self.role_contributor
            )
            self.make_assignment(self.project, self.user_guest, self.role_guest)

    def setUp(self):
        super().setUp()
        self.project_uuid = self.project.sodar_uuid
        self.cat_uuid = self.category.sodar_uuid
        self.url = reverse(
            'projectroles:api_project_destroy',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:api_project_destroy',
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
        ]

    def test_delete(self):
        """Test RoleAssignmentDestroyAPIView DELETE"""
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='DELETE', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    def test_delete_block(self):
        """Test DELETE with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.set_access_block(self.project)  # Need to reset
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    def test_delete_category_with_children(self):
        """Test DELETE for category with children (should fail)"""
        self.assert_response_api(
            self.url_cat,
            self.auth_users,
            403,
            method='DELETE',
        )
        self.assert_response_api(
            self.url_cat, self.anonymous, 401, method='DELETE'
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url_cat, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    def test_delete_category_without_children(self):
        """Test DELETE for category without children"""
        self.project.delete()
        self.assert_response_api(
            self.url_cat,
            self.good_users_cat,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
            cleanup_kwargs={'make_project': False},
        )
        self.assert_response_api(
            self.url_cat,
            self.bad_users_cat,
            403,
            method='DELETE',
        )
        self.assert_response_api(
            self.url_cat, self.anonymous, 401, method='DELETE'
        )

    def test_delete_remote(self):
        """Test DELETE with non-revoked remote project (should fail)"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self.assert_response_api(
            self.url_cat,
            self.auth_users,
            403,
            method='DELETE',
        )
        self.assert_response_api(
            self.url_cat, self.anonymous, 401, method='DELETE'
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url_cat, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    def test_delete_remote_revoked(self):
        """Test DELETE with revoked remote project"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=REMOTE_LEVEL_REVOKED,
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_delete_remote_target(self):
        """Test DELETE with non-revoked remote project as target site (should fail)"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=REMOTE_LEVEL_READ_ROLES,
        )
        self.assert_response_api(
            self.url_cat,
            self.auth_users,
            403,
            method='DELETE',
        )
        self.assert_response_api(
            self.url_cat, self.anonymous, 401, method='DELETE'
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url_cat, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_delete_remote_revoked_target(self):
        """Test DELETE with revoked remote project as target site"""
        site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description='',
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=site,
            level=REMOTE_LEVEL_REVOKED,
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')


class TestRoleAssignmentCreateAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for RoleAssignmentCreateAPIView permissions"""

    def _cleanup(self):
        RoleAssignment.objects.filter(
            project=self.project,
            role__name=SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
            user=self.assign_user,
        ).delete()

    def setUp(self):
        super().setUp()
        self.assign_user = self.make_user('assign_user')
        self.url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.post_data = {
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
            'user': str(self.assign_user.sodar_uuid),
        }
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
        ]

    def test_post(self):
        """Test RoleAssignmentCreateAPIView POST"""
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_block(self):
        """Test POST with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )


class TestRoleAssignmentUpdateAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for RoleAssignmentUpdateAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.assign_user = self.make_user('assign_user')
        update_as = self.make_assignment(
            self.project, self.assign_user, self.role_contributor
        )
        self.url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': update_as.sodar_uuid},
        )
        self.put_data = {
            'role': self.role_guest.name,
            'user': str(self.assign_user.sodar_uuid),
        }
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
        ]

    def test_put(self):
        """Test RoleAssignmentUpdateAPIView PUT"""
        self.assert_response_api(
            self.url, self.good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='PUT',
                data=self.put_data,
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='PUT', data=self.put_data
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.anonymous, 401, method='PUT', data=self.put_data
            )

    def test_put_archive(self):
        """Test PUT with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url, self.good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='PUT',
                data=self.put_data,
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='PUT', data=self.put_data
            )

    def test_put_block(self):
        """Test PUT with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url, self.superuser, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    def test_put_read_only(self):
        """Test PUT with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.superuser, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )


class TestRoleAssignmentDestroyAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for RoleAssignmentDestroyAPIView permissions"""

    def _cleanup(self):
        role_as = self.make_assignment(
            self.project, self.assign_user, self.role_contributor
        )
        role_as.sodar_uuid = self.role_uuid
        role_as.save()

    def setUp(self):
        super().setUp()
        self.assign_user = self.make_user('assign_user')
        self.role_uuid = uuid.uuid4()
        self._cleanup()
        self.url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': self.role_uuid},
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
        ]

    def test_delete(self):
        """Test RoleAssignmentDestroyAPIView DELETE"""
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='DELETE', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    def test_delete_archive(self):
        """Test DELETE with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='DELETE', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='DELETE'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='DELETE'
            )

    def test_delete_block(self):
        """Test DELETE with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_read_only(self):
        """Test DELETE with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')


class TestRoleAssignmentOwnerTransferAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for RoleAssignmentOwnerTransferAPIView permissions"""

    def _cleanup(self):
        self.new_owner_as.refresh_from_db()
        self.new_owner_as.role = self.role_contributor
        self.new_owner_as.save()
        self.owner_as.refresh_from_db()
        self.owner_as.role = self.role_owner
        self.owner_as.save()

    def setUp(self):
        super().setUp()
        self.new_owner = self.make_user('new_owner')
        self.new_owner_as = self.make_assignment(
            self.project, self.new_owner, self.role_contributor
        )
        self.url = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.post_data = {
            'new_owner': self.new_owner.username,
            'old_owner_role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
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
        ]

    def test_post(self):
        """Test RoleAssignmentOwnerTransferAPIView POST"""
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_block(self):
        """Test POST with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )


class TestProjectInviteListAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectInviteListAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_invite_list',
            kwargs={'project': self.project.sodar_uuid},
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
        ]

    def test_get(self):
        """Test ProjectInviteListAPIView GET"""
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestProjectInviteRetrieveAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectInviteRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        self.url = reverse(
            'projectroles:api_invite_retrieve',
            kwargs={'projectinvite': self.invite.sodar_uuid},
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
        ]

    def test_get(self):
        """Test ProjectInviteRetrieveAPIView GET"""
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(self.url, self.user_no_roles, 403)
            self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with archived project and site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestProjectInviteCreateAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectInviteCreateAPIView permissions"""

    def _cleanup(self):
        ProjectInvite.objects.filter(email=self.email).delete()

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.email = 'new@example.com'
        self.post_data = {
            'email': self.email,
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
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
        ]

    def test_post(self):
        """Test ProjectInviteCreateAPIView POST"""
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            201,
            method='POST',
            data=self.post_data,
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_block(self):
        """Test POST with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )


class TestProjectInviteRevokeAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectInviteRevokeAPIView permissions"""

    def _cleanup(self):
        self.invite.active = True
        self.invite.save()

    def setUp(self):
        super().setUp()
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        self.url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
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
        ]

    def test_post(self):
        """Test ProjectInviteRevokeAPIView POST"""
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='POST')
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='POST'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='POST'
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.anonymous, 401, method='POST'
            )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(self.url, self.bad_users, 403, method='POST')
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            knox=True,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='POST'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='POST'
            )

    def test_post_block(self):
        """Test POST with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='POST'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')


class TestProjectInviteResendAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectInviteResendAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        self.url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': self.invite.sodar_uuid},
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
        ]

    def test_post(self):
        """Test ProjectInviteResendAPIView POST"""
        self.assert_response_api(self.url, self.good_users, 200, method='POST')
        self.assert_response_api(self.url, self.bad_users, 403, method='POST')
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='POST'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='POST'
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.anonymous, 401, method='POST'
            )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200, method='POST')
        self.assert_response_api(self.url, self.bad_users, 403, method='POST')
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='POST'
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, method='POST'
            )

    def test_post_block(self):
        """Test POST with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200, method='POST')
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='POST'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.superuser, 200, method='POST')
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='POST'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='POST')


class TestProjectSettingRetrieveAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectSettingRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_project_setting_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        # GET data for PROJECT setting, others defined within tests
        self.get_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_str_setting',
        }
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
        ]

    def test_get_project_setting(self):
        """Test ProjectSettingRetrieveAPIView GET with PROJECT scope"""
        self.assert_response_api(
            self.url, self.good_users, 200, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, data=self.get_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            data=self.get_data,
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, data=self.get_data, knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, data=self.get_data
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, data=self.get_data
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_project_setting_anon(self):
        """Test GET with PROJECT scope and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                [self.user_no_roles, self.anonymous],
                403,
                data=self.get_data,
            )

    def test_get_project_setting_archive(self):
        """Test GET with PROJECT scope and archived project"""
        self.assert_response_api(
            self.url, self.good_users, 200, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, data=self.get_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            data=self.get_data,
            knox=True,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, data=self.get_data, knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, data=self.get_data
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, data=self.get_data
            )

    def test_get_project_setting_block(self):
        """Test GET with PROJECT scope and project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url, self.superuser, 200, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, data=self.get_data
        )

    def test_get_project_setting_read_only(self):
        """Test GET with PROJECT scope and site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.good_users, 200, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, data=self.get_data
        )

    def test_get_project_user_setting(self):
        """Test GET with PROJECT_USER scope"""
        get_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_user_str_setting',
            'user': str(self.user_owner.sodar_uuid),
        }
        good_users = [
            self.superuser,
            self.user_owner,
        ]
        bad_users = [
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
            self.user_no_roles,
        ]
        self.assert_response_api(self.url, good_users, 200, data=get_data)
        self.assert_response_api(self.url, bad_users, 403, data=get_data)
        self.assert_response_api(self.url, self.anonymous, 401, data=get_data)
        self.assert_response_api(
            self.url,
            good_users,
            200,
            data=get_data,
            knox=True,
        )
        self.assert_response_api(
            self.url, bad_users, 403, data=get_data, knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, data=get_data
            )
            self.assert_response_api(
                self.url, self.anonymous, 401, data=self.get_data
            )

    def test_get_project_user_setting_block(self):
        """Test GET with PROJECT scope and project access block"""
        self.set_access_block(self.project)
        get_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_user_str_setting',
            'user': str(self.user_owner.sodar_uuid),
        }
        self.assert_response_api(self.url, self.superuser, 200, data=get_data)
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, data=get_data
        )
        self.assert_response_api(self.url, self.anonymous, 401, data=get_data)

    def test_get_project_user_setting_read_only(self):
        """Test GET with PROJECT_USER scope and site read-only mode"""
        self.set_site_read_only()
        get_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_user_str_setting',
            'user': str(self.user_owner.sodar_uuid),
        }
        good_users = [
            self.superuser,
            self.user_owner,
        ]
        bad_users = [
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
            self.user_no_roles,
        ]
        self.assert_response_api(self.url, good_users, 200, data=get_data)
        self.assert_response_api(self.url, bad_users, 403, data=get_data)
        self.assert_response_api(self.url, self.anonymous, 401, data=get_data)


class TestProjectSettingSetAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for ProjectSettingSetAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_project_setting_set',
            kwargs={'project': self.project.sodar_uuid},
        )
        # POST data for PROJECT setting, others defined within tests
        self.post_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_str_setting',
            'value': 'value',
        }
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
        ]

    def test_post_project_setting(self):
        """Test ProjectSettingSetAPIView POST with PROJECT scope"""
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_project_setting_anon(self):
        """Test POST with PROJECT scope and anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                [self.user_no_roles, self.anonymous],
                403,
                method='POST',
                data=self.post_data,
            )

    def test_post_project_setting_archive(self):
        """Test POST with PROJECT scope and archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.good_users,
            200,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        self.assert_response_api(
            self.url,
            self.bad_users,
            403,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                self.user_no_roles,
                403,
                method='POST',
                data=self.post_data,
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=self.post_data,
            )

    def test_post_project_setting_block(self):
        """Test POST with PROJECT scope and project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_project_setting_read_only(self):
        """Test POST with PROJECT scope and site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_project_user_setting(self):
        """Test POST with PROJECT_USER scope"""
        post_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_user_str_setting',
            'value': 'value',
            'user': str(self.user_owner.sodar_uuid),
        }
        good_users = [self.superuser, self.user_owner]
        bad_users = [
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
            self.user_no_roles,
        ]
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='POST',
            data=post_data,
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=post_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='POST',
            data=post_data,
            knox=True,
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, self.user_no_roles, 403, method='POST', data=post_data
            )
            self.assert_response_api(
                self.url,
                self.anonymous,
                401,
                method='POST',
                data=post_data,
            )

    def test_post_project_user_setting_block(self):
        """Test POST with PROJECT_USER scope and project access block"""
        self.set_access_block(self.project)
        post_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_user_str_setting',
            'value': 'value',
            'user': str(self.user_owner.sodar_uuid),
        }
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            data=post_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_post_project_user_setting_read_only(self):
        """Test POST with PROJECT_USER scope and site read-only mode"""
        self.set_site_read_only()
        post_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'project_user_str_setting',
            'value': 'value',
            'user': str(self.user_owner.sodar_uuid),
        }
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='POST',
            data=post_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='POST',
            data=post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=post_data
        )


class TestUserSettingRetrieveAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for UserSettingRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_user_setting_retrieve')
        self.get_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'user_str_setting',
        }

    def test_get(self):
        """Test UserSettingRetrieveAPIView GET"""
        self.assert_response_api(
            self.url, self.auth_non_superusers, 200, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 403, data=self.get_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            200,
            data=self.get_data,
            knox=True,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url, [self.anonymous], 403, data=self.get_data
            )

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.auth_non_superusers, 200, data=self.get_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 403, data=self.get_data
        )


class TestUserSettingSetAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for UserSettingSetAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_user_setting_set')
        self.post_data = {
            'plugin_name': APP_NAME_EX,
            'setting_name': 'user_str_setting',
            'value': 'value',
        }

    def test_post(self):
        """Test UserSettingSetAPIView POST"""
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            200,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            200,
            method='POST',
            data=self.post_data,
            knox=True,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        for role in self.guest_roles:
            self.project.set_public_access(role)
            self.assert_response_api(
                self.url,
                [self.anonymous],
                403,
                method='POST',
                data=self.post_data,
            )

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            200,
            method='POST',
            data=self.post_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 403, method='POST', data=self.post_data
        )


class TestUserListAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for UserListAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_user_list')

    def test_get(self):
        """Test UserListAPIView GET"""
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.auth_users, 200, knox=True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response_api(self.url, [self.anonymous], 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_API_USER_DETAIL_RESTRICT=True)
    def test_get_restrict(self):
        """Test GET with user detail access restriction"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        bad_users = [
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
        ]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestUserRetrieveAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for UserRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_user_retrieve',
            kwargs={'user': self.superuser.sodar_uuid},
        )

    def test_get(self):
        """Test UserRetrieveAPIView GET"""
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.auth_users, 200, knox=True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response_api(self.url, [self.anonymous], 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_API_USER_DETAIL_RESTRICT=True)
    def test_get_restrict(self):
        """Test GET with user detail access restriction"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_viewer,
        ]
        bad_users = [self.user_no_roles]
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestCurrentUserRetrieveAPIView(ProjectrolesAPIPermissionTestBase):
    """Tests for CurrentUserRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_user_current')

    def test_get(self):
        """Test CurrentUserRetrieveAPIView GET"""
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.auth_users, 200, knox=True)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.assert_response_api(self.url, [self.anonymous], 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.auth_users, 200)
        self.assert_response_api(self.url, self.anonymous, 401)
