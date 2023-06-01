"""REST API view permission tests for the projectroles app"""

import uuid

from django.test import override_settings
from django.urls import reverse

from projectroles.models import (
    Project,
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    SODAR_CONSTANTS,
)
from projectroles.tests.test_permissions import TestProjectPermissionBase
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.views_api import CORE_API_MEDIA_TYPE, CORE_API_DEFAULT_VERSION

from rest_framework.test import APITestCase


NEW_PROJECT_TITLE = 'New Project'


# Base Classes and Mixins ------------------------------------------------------


class SODARAPIPermissionTestMixin(SODARAPIViewTestMixin):
    """Mixin for permission testing with knox auth"""

    def assert_response_api(
        self,
        url,
        users,
        status_code,
        method='GET',
        format='json',
        data=None,
        media_type=None,
        version=None,
        knox=False,
        cleanup_method=None,
        cleanup_kwargs=None,
        req_kwargs=None,
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

        def _send_request():
            req_method = getattr(self.client, method.lower(), None)
            if not req_method:
                raise ValueError('Invalid method "{}"'.format(method))
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

            msg = 'user={}; content="{}"'.format(user, response.content)
            self.assertEqual(response.status_code, status_code, msg=msg)

            if cleanup_method:
                if cleanup_kwargs is None:
                    cleanup_kwargs = {}
                cleanup_method(**cleanup_kwargs)


class TestProjectAPIPermissionBase(
    SODARAPIPermissionTestMixin, APITestCase, TestProjectPermissionBase
):
    """Base class for testing project permissions in SODAR API views"""


class TestCoreProjectAPIPermissionBase(
    SODARAPIPermissionTestMixin, APITestCase, TestProjectPermissionBase
):
    """
    Base class for testing project permissions in internal SODAR Core API views
    """

    media_type = CORE_API_MEDIA_TYPE
    api_version = CORE_API_DEFAULT_VERSION


# Tests ------------------------------------------------------------------------


class TestAPIPermissions(TestCoreProjectAPIPermissionBase):
    """Tests for projectroles API view permissions"""

    def test_project_list(self):
        """Test ProjectListAPIView permissions"""
        url = reverse('projectroles:api_project_list')
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
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)

    def test_project_retrieve(self):
        """Test ProjectRetrieveAPIView permissions"""
        url = reverse(
            'projectroles:api_project_retrieve',
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
        bad_users = [self.user_finder_cat, self.user_no_roles]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        self.assert_response_api(url, bad_users, 403, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_retrieve_anon(self):
        """Test ProjectRetrieveAPIView permissions with anonymous access"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_project_create_root(self):
        """Test ProjectCreateAPIView permissions with no parent"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'],
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
        }
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
        ]

        def _cleanup():
            p = Project.objects.filter(title=NEW_PROJECT_TITLE).first()
            if p:
                p.delete()

        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_create_root_anon(self):
        """Test ProjectCreateAPIView permission with no parent and anon access"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY'],
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_project_create(self):
        """Test ProjectCreateAPIView permissions"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
        }

        def _cleanup():
            p = Project.objects.filter(title=NEW_PROJECT_TITLE).first()
            if p:
                p.delete()

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
        ]
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_create_anon(self):
        """Test ProjectCreateAPIView permissions with anonymous access"""
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_project_update(self):
        """Test ProjectUpdateAPIView permissions"""
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        put_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
        }
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
        ]
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )
        # Test with Knox
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data, knox=True
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_update_anon(self):
        """Test ProjectUpdateAPIView permissions with anonymous access"""
        url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        put_data = {
            'title': NEW_PROJECT_TITLE,
            'type': SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'],
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'owner': str(self.user_owner.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )

    def test_role_create(self):
        """Test RoleAssignmentCreateAPIView permissions"""
        # Create user for assignments
        assign_user = self.make_user('assign_user')
        url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
            'user': str(assign_user.sodar_uuid),
        }
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
        ]

        def _cleanup():
            role_as = RoleAssignment.objects.filter(
                project=self.project,
                role__name=SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
                user=assign_user,
            ).first()
            if role_as:
                role_as.delete()

        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_create_anon(self):
        """Test RoleAssignmentCreateAPIView permissions with anonymous access"""
        assign_user = self.make_user('assign_user')
        url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
            'user': str(assign_user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_role_update(self):
        """Test RoleAssignmentUpdateAPIView permissions"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        update_as = self.make_assignment(
            self.project, assign_user, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': update_as.sodar_uuid},
        )
        put_data = {
            'role': self.role_guest.name,
            'user': str(assign_user.sodar_uuid),
        }
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
        ]
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )
        # Test with Knox
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=put_data, knox=True
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=put_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_update_anon(self):
        """Test RoleAssignmentUpdateAPIView permissions with anonymous access"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        update_as = self.make_assignment(
            self.project, assign_user, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': update_as.sodar_uuid},
        )
        put_data = {
            'role': self.role_guest.name,
            'user': str(assign_user.sodar_uuid),
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=put_data
        )

    def test_role_delete(self):
        """Test RoleAssignmentDestroyAPIView permissions"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        role_uuid = uuid.uuid4()  # Ensure fixed uuid

        def _cleanup():
            update_as = self.make_assignment(
                self.project, assign_user, self.role_contributor
            )
            update_as.sodar_uuid = role_uuid
            update_as.save()

        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': role_uuid},
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
        ]
        _cleanup()
        self.assert_response_api(
            url, good_users, 204, method='DELETE', cleanup_method=_cleanup
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=_cleanup,
            knox=True,
        )
        self.assert_response_api(
            url, bad_users, 403, method='DELETE', knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='DELETE')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_role_delete_anon(self):
        """Test RoleAssignmentDestroyAPIView permissions with anon access"""
        # Create user and assignment
        assign_user = self.make_user('assign_user')
        role_uuid = uuid.uuid4()  # Ensure fixed uuid
        update_as = self.make_assignment(
            self.project, assign_user, self.role_contributor
        )
        update_as.sodar_uuid = role_uuid
        update_as.save()
        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': role_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')

    def test_owner_transfer(self):
        """Test RoleAssignmentOwnerTransferAPIView permissions"""
        # Create user for assignments
        self.new_owner = self.make_user('new_owner')
        self.new_owner_as = self.make_assignment(
            self.project, self.new_owner, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'new_owner': self.new_owner.username,
            'old_owner_role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }

        def _cleanup():
            self.new_owner_as.refresh_from_db()
            self.new_owner_as.role = self.role_contributor
            self.new_owner_as.save()

            self.owner_as.refresh_from_db()
            self.owner_as.role = self.role_owner
            self.owner_as.save()

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
        ]
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_owner_transfer_anon(self):
        """Test RoleAssignmentOwnerTransferAPIView with anon access"""
        # Create user for assignments
        self.new_owner = self.make_user('new_owner')
        self.new_owner_as = self.make_assignment(
            self.project, self.new_owner, self.role_contributor
        )
        url = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'new_owner': self.new_owner.username,
            'old_owner_role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_invite_list(self):
        """Test ProjectInviteListAPIView permissions"""
        url = reverse(
            'projectroles:api_invite_list',
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
        ]
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_list_anon(self):
        """Test ProjectInviteListAPIView permissions with anonymous access"""
        url = reverse(
            'projectroles:api_invite_list',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401)

    def test_invite_create(self):
        """Test ProjectInviteCreateAPIView permissions"""
        email = 'new@example.com'
        url = reverse(
            'projectroles:api_invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'email': email,
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
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
        ]

        def _cleanup():
            invite = ProjectInvite.objects.filter(
                email=email,
            ).first()
            if invite:
                invite.delete()

        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_create_anon(self):
        """Test ProjectInviteCreateAPIView permissions with anonymous access"""
        email = 'new@example.com'
        url = reverse(
            'projectroles:api_invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'email': email,
            'role': SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR'],
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )

    def test_invite_revoke(self):
        """Test ProjectInviteRevokeAPIView permissions"""
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
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
        ]

        def _cleanup():
            self.invite.active = True
            self.invite.save()

        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='POST',
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, bad_users, 403, method='POST', knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_revoke_anon(self):
        """Test ProjectInviteRevokeAPIView permissions with anonymous access"""
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='POST')

    def test_invite_resend(self):
        """Test ProjectInviteResendAPIView permissions with anonymous access"""
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': self.invite.sodar_uuid},
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
        ]
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='POST',
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            knox=True,
        )
        self.assert_response_api(url, bad_users, 403, method='POST', knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_invite_resend_anon(self):
        """Test permissions for ProjectInviteResendAPIView with anonymous access"""
        self.invite = self.make_invite(
            email='new@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
        )
        url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='POST')

    def test_project_setting_retrieve(self):
        """Test ProjectSettingRetrieveAPIView permissions"""
        url = reverse(
            'projectroles:api_project_setting_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        get_data = {
            'app_name': 'example_project_app',
            'setting_name': 'project_str_setting',
        }
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
        ]

        def _cleanup():
            AppSetting.objects.all().delete()

        self.assert_response_api(
            url,
            good_users,
            200,
            data=get_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, bad_users, 403, data=get_data)
        self.assert_response_api(url, self.anonymous, 401, data=get_data)
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            data=get_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, bad_users, 403, data=get_data, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, data=get_data)

    def test_project_setting_retrieve_user(self):
        """Test ProjectSettingRetrieveAPIView permissions with PROJECT_USER setting"""
        url = reverse(
            'projectroles:api_project_setting_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        get_data = {
            'app_name': 'example_project_app',
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
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]

        def _cleanup():
            AppSetting.objects.all().delete()

        self.assert_response_api(
            url,
            good_users,
            200,
            data=get_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, bad_users, 403, data=get_data)
        self.assert_response_api(url, self.anonymous, 401, data=get_data)
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            data=get_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, bad_users, 403, data=get_data, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, data=get_data)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_setting_retrieve_anon(self):
        """Test ProjectSettingRetrieveAPIView permissions with anonymous access"""
        url = reverse(
            'projectroles:api_project_setting_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        get_data = {
            'app_name': 'example_project_app',
            'setting_name': 'project_str_setting',
        }
        self.project.set_public()
        self.assert_response_api(
            url,
            [self.user_no_roles, self.anonymous],
            403,
            data=get_data,
        )

    def test_project_setting_set(self):
        """Test ProjectSettingSetAPIView permissions"""
        url = reverse(
            'projectroles:api_project_setting_set',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'app_name': 'example_project_app',
            'setting_name': 'project_str_setting',
            'value': 'value',
        }
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
        ]

        def _cleanup():
            AppSetting.objects.all().delete()

        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    def test_project_setting_set_user(self):
        """Test ProjectSettingSetAPIView permissions with PROJECT_USER scope"""
        url = reverse(
            'projectroles:api_project_setting_set',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'app_name': 'example_project_app',
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
            self.user_finder_cat,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]

        def _cleanup():
            AppSetting.objects.all().delete()

        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=post_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_project_setting_set_anon(self):
        """Test ProjectSettingSetAPIView permissions with anonymous access"""
        url = reverse(
            'projectroles:api_project_setting_set',
            kwargs={'project': self.project.sodar_uuid},
        )
        post_data = {
            'app_name': 'example_project_app',
            'setting_name': 'project_str_setting',
            'value': 'value',
        }
        self.project.set_public()
        self.assert_response_api(
            url,
            [self.user_no_roles, self.anonymous],
            403,
            method='POST',
            data=post_data,
        )

    def test_user_setting_retrieve(self):
        """Test UserSettingRetrieveAPIView permissions"""
        url = reverse('projectroles:api_user_setting_retrieve')
        get_data = {
            'app_name': 'example_project_app',
            'setting_name': 'user_str_setting',
        }
        good_users = [
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

        def _cleanup():
            AppSetting.objects.all().delete()

        self.assert_response_api(
            url,
            good_users,
            200,
            data=get_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(url, self.anonymous, 403, data=get_data)
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            data=get_data,
            knox=True,
            cleanup_method=_cleanup,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_user_setting_retrieve_anon(self):
        """Test UserSettingRetrieveAPIView permissions with anonymous access"""
        url = reverse('projectroles:api_user_setting_retrieve')
        get_data = {
            'app_name': 'example_project_app',
            'setting_name': 'user_str_setting',
        }
        self.assert_response_api(
            url,
            [self.anonymous],
            403,
            data=get_data,
        )

    def test_user_setting_set(self):
        """Test UserSettingSetAPIView permissions"""
        url = reverse('projectroles:api_user_setting_set')
        post_data = {
            'app_name': 'example_project_app',
            'setting_name': 'user_str_setting',
            'value': 'value',
        }
        good_users = [
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

        def _cleanup():
            AppSetting.objects.all().delete()

        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            cleanup_method=_cleanup,
        )
        self.assert_response_api(
            url, self.anonymous, 403, method='POST', data=post_data
        )
        # Test with Knox
        self.assert_response_api(
            url,
            good_users,
            200,
            method='POST',
            data=post_data,
            knox=True,
            cleanup_method=_cleanup,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_user_setting_set_anon(self):
        """Test UserSettingSetAPIView permissions with anonymous access"""
        url = reverse('projectroles:api_user_setting_set')
        post_data = {
            'app_name': 'example_project_app',
            'setting_name': 'user_str_setting',
            'value': 'value',
        }
        self.project.set_public()
        self.assert_response_api(
            url,
            [self.anonymous],
            403,
            method='POST',
            data=post_data,
        )

    def test_user_list(self):
        """Test permissions for UserListAPIView"""
        url = reverse('projectroles:api_user_list')
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
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)

    def test_user_current(self):
        """Test permissions for CurrentUserRetrieveAPIView"""
        url = reverse('projectroles:api_user_current')
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
        self.assert_response_api(url, good_users, 200)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
