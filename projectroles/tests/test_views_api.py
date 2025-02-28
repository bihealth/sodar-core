"""REST API view tests for the projectroles app"""

import base64
import json
import pytz

from knox.models import AuthToken

from django.conf import settings
from django.contrib.auth.models import Group
from django.core import mail
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from test_plus.test import APITestCase

# Timeline dependency
from timeline.models import TimelineEvent

from projectroles import views_api
from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    SODARUserAdditionalEmail,
    SODAR_CONSTANTS,
    AUTH_TYPE_LDAP,
    AUTH_TYPE_LOCAL,
    CAT_DELIMITER,
)
from projectroles.plugins import get_backend_api
from projectroles.remote_projects import RemoteProjectAPI
from projectroles.tests.test_app_settings import AppSettingInitMixin
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    SODARUserAdditionalEmailMixin,
    ADD_EMAIL,
)
from projectroles.tests.test_views import (
    ViewTestBase,
    REMOTE_SITE_NAME,
    REMOTE_SITE_URL,
    REMOTE_SITE_DESC,
    REMOTE_SITE_SECRET,
)
from projectroles.utils import build_secret


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_ROLE_FINDER = SODAR_CONSTANTS['PROJECT_ROLE_FINDER']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
APP_NAME = 'projectroles'
CORE_API_MEDIA_TYPE_LEGACY = 'application/vnd.bihealth.sodar-core+json'
CORE_API_DEFAULT_VERSION_LEGACY = '0.13.4'
CORE_API_MEDIA_TYPE_INVALID = 'application/vnd.bihealth.invalid'
CORE_API_VERSION_INVALID = '9.9.9'

INVALID_UUID = '11111111-1111-1111-1111-111111111111'
NEW_CATEGORY_TITLE = 'New Category'
NEW_PROJECT_TITLE = 'New Project'
UPDATED_TITLE = 'Updated Title'
UPDATED_DESC = 'Updated description'
UPDATED_README = 'Updated readme'

INVITE_USER_EMAIL = 'new1@example.com'
INVITE_USER2_EMAIL = 'new2@example.com'
INVITE_MESSAGE = 'Message'

# Special value to use for empty knox token
EMPTY_KNOX_TOKEN = '__EmpTy_KnoX_tOkEn_FoR_tEsT_oNlY_0xDEADBEEF__'

EX_APP_NAME = 'example_project_app'
TEST_SERVER_URL = 'http://testserver'
LDAP_DOMAIN = 'EXAMPLE'


# Base Classes -----------------------------------------------------------------


class SerializedObjectMixin:
    """
    Mixin for helpers with serialized objects.
    """

    @classmethod
    def get_serialized_user(cls, user):
        """
        Return serialization for a user.

        :param user: User object
        :return: Dict
        """
        add_emails = SODARUserAdditionalEmail.objects.filter(
            user=user, verified=True
        ).order_by('email')
        return {
            'additional_emails': [e.email for e in add_emails],
            'auth_type': user.get_auth_type(),
            'email': user.email,
            'is_superuser': user.is_superuser,
            'name': user.name,
            'sodar_uuid': str(user.sodar_uuid),
            'username': user.username,
        }


class SODARAPIViewTestMixin(SerializedObjectMixin):
    """
    Mixin for SODAR and SODAR Core API views with accept headers, knox token
    authorization and general helper methods.
    """

    # Copied from Knox tests
    @classmethod
    def get_basic_auth_header(cls, username, password):
        return (
            'Basic %s'
            % base64.b64encode(
                ('%s:%s' % (username, password)).encode('ascii')
            ).decode()
        )

    @classmethod
    def get_token(cls, user, full_result=False):
        """
        Get or create a knox token for a user.

        :param user: User object
        :param full_result: Return full result of AuthToken creation if True
        :return: Token string or AuthToken creation tuple (EMPTY_KNOX_TOKEN if
                 user is None)
        """
        if user is None:
            return EMPTY_KNOX_TOKEN
        result = AuthToken.objects.create(user=user)
        return result if full_result else result[1]

    @classmethod
    def get_drf_datetime(cls, obj_dt):
        """
        Return datetime in DRF compatible format.

        :param obj_dt: Object DateTime field
        :return: String
        """
        return timezone.localtime(
            obj_dt, pytz.timezone(settings.TIME_ZONE)
        ).isoformat()

    @classmethod
    def get_accept_header(
        cls,
        media_type=None,
        version=None,
    ):
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
        return {'HTTP_ACCEPT': '{}; version={}'.format(media_type, version)}

    @classmethod
    def get_token_header(cls, token):
        """
        Return auth header based on token.

        :param token: Token string
        :return: Dict, empty if token is None
        """
        if token is EMPTY_KNOX_TOKEN:
            return {}
        else:
            return {'HTTP_AUTHORIZATION': 'token {}'.format(token)}

    def request_knox(
        self,
        url,
        method='GET',
        format='json',
        data=None,
        token=None,
        media_type=None,
        version=None,
        header=None,
    ):
        """
        Perform a HTTP request with Knox token auth.

        :param url: URL for the request
        :param method: Request method (string, default="GET")
        :param format: Request format (string, default="json")
        :param data: Optional data for request (dict)
        :param token: Knox token string (if None, use self.knox_token)
        :param media_type: String (default = cls.media_type)
        :param version: String (default = cls.api_version)
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
            raise ValueError('Unsupported method "{}"'.format(method))
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


class ProjectrolesAPIViewTestBase(APIViewTestBase):
    """Override of APIViewTestBase to be used with Projectroles API views"""

    media_type = views_api.PROJECTROLES_API_MEDIA_TYPE
    api_version = views_api.PROJECTROLES_API_DEFAULT_VERSION


# Tests ------------------------------------------------------------------------


class TestProjectListAPIView(ProjectrolesAPIViewTestBase):
    """Tests for ProjectListAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_project_list')

    def test_get(self):
        """Test ProjectListAPIView GET as superuser"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        expected = [
            {
                'title': self.category.title,
                'type': self.category.type,
                'parent': None,
                'description': self.category.description,
                'readme': '',
                'public_guest_access': False,
                'archive': False,
                'full_title': self.category.full_title,
                'roles': {
                    str(self.owner_as_cat.sodar_uuid): {
                        'user': self.get_serialized_user(self.user_owner_cat),
                        'role': PROJECT_ROLE_OWNER,
                        'inherited': False,
                        'sodar_uuid': str(self.owner_as_cat.sodar_uuid),
                    }
                },
                'children': [str(self.project.sodar_uuid)],
                'sodar_uuid': str(self.category.sodar_uuid),
            },
            {
                'title': self.project.title,
                'type': self.project.type,
                'parent': str(self.category.sodar_uuid),
                'description': self.project.description,
                'readme': '',
                'public_guest_access': False,
                'archive': False,
                'full_title': self.project.full_title,
                'roles': {
                    str(self.owner_as_cat.sodar_uuid): {
                        'user': self.get_serialized_user(self.user_owner_cat),
                        'role': PROJECT_ROLE_OWNER,
                        'inherited': True,
                        'sodar_uuid': str(self.owner_as_cat.sodar_uuid),
                    },
                    str(self.owner_as.sodar_uuid): {
                        'user': self.get_serialized_user(self.user_owner),
                        'role': PROJECT_ROLE_OWNER,
                        'inherited': False,
                        'sodar_uuid': str(self.owner_as.sodar_uuid),
                    },
                },
                'sodar_uuid': str(self.project.sodar_uuid),
            },
        ]
        self.assertEqual(response_data, expected)

    def test_get_cat_owner(self):
        """Test GET as category owner"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_owner_cat)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)

    def test_get_owner(self):
        """Test GET as project owner"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_owner)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(
            response_data[0]['sodar_uuid'], str(self.project.sodar_uuid)
        )

    def test_get_no_roles(self):
        """Test GET without roles"""
        user_new = self.make_user('user_new')
        response = self.request_knox(self.url, token=self.get_token(user_new))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 0)

    def test_get_member(self):
        """Test GET with only local role"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.project, user_new, self.role_contributor)
        response = self.request_knox(self.url, token=self.get_token(user_new))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(
            response_data[0]['sodar_uuid'], str(self.project.sodar_uuid)
        )

    def test_get_inherited_member(self):
        """Test GET with inherited member role"""
        sub_category = self.make_project(
            'SubCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(sub_category, self.user_owner, self.role_owner)
        sub_project = self.make_project(
            'SubProject', PROJECT_TYPE_PROJECT, sub_category
        )
        self.make_assignment(sub_project, self.user_owner, self.role_owner)
        user_new = self.make_user('user_new')
        self.make_assignment(self.category, user_new, self.role_contributor)
        response = self.request_knox(self.url, token=self.get_token(user_new))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 4)

    def test_get_finder(self):
        """Test GET with finder"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.category, user_new, self.role_finder)
        response = self.request_knox(self.url, token=self.get_token(user_new))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        self.assertEqual(
            response_data[0]['sodar_uuid'], str(self.category.sodar_uuid)
        )
        self.assertEqual(
            response_data[1]['sodar_uuid'], str(self.project.sodar_uuid)
        )
        self.assertEqual(
            response_data[1],
            {
                'title': self.project.title,
                'full_title': self.project.full_title,
                'sodar_uuid': str(self.project.sodar_uuid),
            },
        )

    def test_get_public_guest_access(self):
        """Test GET with public guest access"""
        self.project.public_guest_access = True
        self.project.save()
        user_new = self.make_user('user_new')
        response = self.request_knox(self.url, token=self.get_token(user_new))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(
            response_data[0]['sodar_uuid'], str(self.project.sodar_uuid)
        )

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'count': 2,
            'next': TEST_SERVER_URL + self.url + '?page=2',
            'previous': None,
            'results': [
                {
                    'title': self.category.title,
                    'type': self.category.type,
                    'parent': None,
                    'description': self.category.description,
                    'readme': '',
                    'public_guest_access': False,
                    'archive': False,
                    'full_title': self.category.full_title,
                    'roles': {
                        str(self.owner_as_cat.sodar_uuid): {
                            'user': self.get_serialized_user(
                                self.user_owner_cat
                            ),
                            'role': PROJECT_ROLE_OWNER,
                            'inherited': False,
                            'sodar_uuid': str(self.owner_as_cat.sodar_uuid),
                        }
                    },
                    'children': [str(self.project.sodar_uuid)],
                    'sodar_uuid': str(self.category.sodar_uuid),
                }
            ],
        }
        self.assertEqual(response_data, expected)


class TestProjectRetrieveAPIView(AppSettingMixin, ProjectrolesAPIViewTestBase):
    """Tests for ProjectRetrieveAPIView"""

    def test_get_category(self):
        """Test ProjectRetrieveAPIView GET with category"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.category.sodar_uuid},
        )
        response = self.request_knox(url)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'title': self.category.title,
            'type': self.category.type,
            'parent': None,
            'description': self.category.description,
            'readme': '',
            'public_guest_access': False,
            'archive': False,
            'full_title': self.category.full_title,
            'roles': {
                str(self.owner_as_cat.sodar_uuid): {
                    'user': self.get_serialized_user(self.user_owner_cat),
                    'role': PROJECT_ROLE_OWNER,
                    'inherited': False,
                    'sodar_uuid': str(self.owner_as_cat.sodar_uuid),
                }
            },
            'children': [str(self.project.sodar_uuid)],
            'sodar_uuid': str(self.category.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_project(self):
        """Test GET with project"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        response = self.request_knox(url)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'title': self.project.title,
            'type': self.project.type,
            'parent': str(self.category.sodar_uuid),
            'description': self.project.description,
            'readme': '',
            'public_guest_access': False,
            'archive': False,
            'full_title': self.project.full_title,
            'roles': {
                str(self.owner_as_cat.sodar_uuid): {
                    'user': self.get_serialized_user(self.user_owner_cat),
                    'role': PROJECT_ROLE_OWNER,
                    'inherited': True,
                    'sodar_uuid': str(self.owner_as_cat.sodar_uuid),
                },
                str(self.owner_as.sodar_uuid): {
                    'user': self.get_serialized_user(self.user_owner),
                    'role': PROJECT_ROLE_OWNER,
                    'inherited': False,
                    'sodar_uuid': str(self.owner_as.sodar_uuid),
                },
            },
            'sodar_uuid': str(self.project.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_not_found(self):
        """Test GET with invalid UUID"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': INVALID_UUID},
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 404)

    def test_get_inherited_member(self):
        """Test GET with inherited member"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.category, user_new, self.role_contributor)
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data['roles']), 3)

    def test_get_category_v1_0(self):
        """Test GET with category and API version v1.0"""
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.category.sodar_uuid},
        )
        response = self.request_knox(url, version='1.0')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertNotIn('children', response_data)


class TestProjectCreateAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectCreateAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_project_create')

    def test_post_category(self):
        """Test ProjectCreateAPIView POST for root category"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)
        # Assert object content
        new_category = Project.objects.get(title=NEW_CATEGORY_TITLE)
        model_dict = model_to_dict(new_category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': new_category.pk,
            'title': new_category.title,
            'type': new_category.type,
            'parent': None,
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'public_guest_access': False,
            'archive': False,
            'full_title': new_category.title,
            'has_public_children': False,
            'sodar_uuid': new_category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)
        # Assert role assignment
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=new_category, user=self.user, role=self.role_owner
            ).count(),
            1,
        )
        # Assert API response
        expected = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'public_guest_access': False,
            'full_title': new_category.full_title,
            'sodar_uuid': str(new_category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_category_nested(self):
        """Test POST for category under existing category"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)
        new_category = Project.objects.get(title=NEW_CATEGORY_TITLE)
        model_dict = model_to_dict(new_category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': new_category.pk,
            'title': new_category.title,
            'type': new_category.type,
            'parent': self.category.pk,
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'public_guest_access': False,
            'archive': False,
            'full_title': self.category.title
            + CAT_DELIMITER
            + new_category.title,
            'has_public_children': False,
            'sodar_uuid': new_category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=new_category, user=self.user, role=self.role_owner
            ).count(),
            1,
        )
        expected = {
            'title': NEW_CATEGORY_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': str(self.category.sodar_uuid),
            'description': new_category.description,
            'readme': new_category.readme.raw,
            'public_guest_access': False,
            'full_title': new_category.full_title,
            'sodar_uuid': str(new_category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_project(self):
        """Test POST for project under existing category"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)
        new_project = Project.objects.get(title=NEW_PROJECT_TITLE)
        model_dict = model_to_dict(new_project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': new_project.pk,
            'title': new_project.title,
            'type': new_project.type,
            'parent': self.category.pk,
            'description': new_project.description,
            'readme': new_project.readme.raw,
            'public_guest_access': False,
            'archive': False,
            'full_title': self.category.title
            + CAT_DELIMITER
            + new_project.title,
            'has_public_children': False,
            'sodar_uuid': new_project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=new_project, user=self.user, role=self.role_owner
            ).count(),
            1,
        )
        expected = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': new_project.description,
            'readme': new_project.readme.raw,
            'public_guest_access': False,
            'full_title': new_project.full_title,
            'sodar_uuid': str(new_project.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_project_root(self):
        """Test POST for project in root (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': None,
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    @override_settings(PROJECTROLES_DISABLE_CATEGORIES=True)
    def test_post_project_disable_categories(self):
        """Test POST for project in root with disabled categories"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': '',
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)

    def test_post_project_duplicate_title(self):
        """Test POST for project with title already in category (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': self.project.title,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_post_project_title_delimiter(self):
        """Test POST for project with category delimiter in title (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': 'New{}Project'.format(CAT_DELIMITER),
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_post_project_unknown_user(self):
        """Test POST for project with non-existent user (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': INVALID_UUID,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_post_project_unknown_parent(self):
        """Test POST for project with non-existent parent (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': INVALID_UUID,
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    def test_post_project_invalid_parent(self):
        """Test POST for project with project as parent (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.project.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Project.objects.count(), 2)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_project_target_enabled(self):
        """Test POST for project as TARGET with target creation allowed"""
        self.assertEqual(Project.objects.count(), 2)
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.count(), 3)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_project_target_remote(self):
        """Test POST for project as TARGET under remote category (should fail)"""
        # Create source site
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        # Make category remote
        self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.assertEqual(Project.objects.count(), 2)

        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 403, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

    @override_settings(
        PROJECTROLES_SITE_MODE=SITE_MODE_TARGET,
        PROJECTROLES_TARGET_CREATE=False,
    )
    def test_post_project_target_disabled(self):
        """Test POST for project as TARGET with target creation disallowed (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        url = reverse('projectroles:api_project_create')
        post_data = {
            'title': NEW_PROJECT_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': 'description',
            'readme': 'readme',
            'public_guest_access': False,
            'owner': str(self.user.sodar_uuid),
        }
        response = self.request_knox(url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 403, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)


class TestProjectUpdateAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectUpdateAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:api_project_update',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_put_category(self):
        """Test ProjectUpdateAPIView PUT with category"""
        self.assertEqual(Project.objects.count(), 2)
        put_data = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': False,
        }
        response = self.request_knox(self.url_cat, method='PUT', data=put_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        self.category.refresh_from_db()
        model_dict = model_to_dict(self.category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.category.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': False,
            'archive': False,
            'full_title': UPDATED_TITLE,
            'has_public_children': False,
            'sodar_uuid': self.category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': False,
            'archive': False,
            'full_title': UPDATED_TITLE,
            'roles': {
                str(self.category.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user_owner_cat),
                    'inherited': False,
                    'sodar_uuid': str(self.category.get_owner().sodar_uuid),
                }
            },
            'children': [str(self.project.sodar_uuid)],
            'sodar_uuid': str(self.category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_put_public_guest_access_category(self):
        """Test PUT to set public guest access for category (should fail)"""
        put_data = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': '',
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
        }
        response = self.request_knox(self.url_cat, method='PUT', data=put_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_put_project(self):
        """Test PUT with project"""
        self.assertEqual(Project.objects.count(), 2)
        put_data = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
        }
        response = self.request_knox(self.url, method='PUT', data=put_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.project.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
            'archive': False,
            'full_title': self.category.title + CAT_DELIMITER + UPDATED_TITLE,
            'has_public_children': False,
            'sodar_uuid': self.project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
            'archive': False,
            'full_title': self.category.title + CAT_DELIMITER + UPDATED_TITLE,
            'roles': {
                str(self.category.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user_owner_cat),
                    'inherited': True,
                    'sodar_uuid': str(self.category.get_owner().sodar_uuid),
                },
                str(self.project.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user_owner),
                    'inherited': False,
                    'sodar_uuid': str(self.project.get_owner().sodar_uuid),
                },
            },
            'sodar_uuid': str(self.project.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_category(self):
        """Test PATCH with category"""
        self.assertEqual(Project.objects.count(), 2)
        patch_data = {
            'title': UPDATED_TITLE,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
        }
        response = self.request_knox(
            self.url_cat, method='PATCH', data=patch_data
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        self.category.refresh_from_db()
        model_dict = model_to_dict(self.category)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.category.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': False,
            'archive': False,
            'full_title': UPDATED_TITLE,
            'has_public_children': False,
            'sodar_uuid': self.category.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)

        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_CATEGORY,
            'parent': None,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': False,
            'archive': False,
            'full_title': UPDATED_TITLE,
            'roles': {
                str(self.category.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user_owner_cat),
                    'inherited': False,
                    'sodar_uuid': str(self.category.get_owner().sodar_uuid),
                }
            },
            'children': [str(self.project.sodar_uuid)],
            'sodar_uuid': str(self.category.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_project(self):
        """Test PATCH with project"""
        self.assertEqual(Project.objects.count(), 2)
        patch_data = {
            'title': UPDATED_TITLE,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
        }
        response = self.request_knox(self.url, method='PATCH', data=patch_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)

        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        model_dict['readme'] = model_dict['readme'].raw
        expected = {
            'id': self.project.pk,
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': self.category.pk,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
            'archive': False,
            'full_title': self.category.title + CAT_DELIMITER + UPDATED_TITLE,
            'has_public_children': False,
            'sodar_uuid': self.project.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)
        self.assertEqual(self.project.get_owner().user, self.user_owner)

        expected = {
            'title': UPDATED_TITLE,
            'type': PROJECT_TYPE_PROJECT,
            'parent': str(self.category.sodar_uuid),
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
            'public_guest_access': True,
            'archive': False,
            'full_title': self.category.title + CAT_DELIMITER + UPDATED_TITLE,
            'roles': {
                str(self.category.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user_owner_cat),
                    'inherited': True,
                    'sodar_uuid': str(self.category.get_owner().sodar_uuid),
                },
                str(self.project.get_owner().sodar_uuid): {
                    'role': PROJECT_ROLE_OWNER,
                    'user': self.get_serialized_user(self.user_owner),
                    'inherited': False,
                    'sodar_uuid': str(self.project.get_owner().sodar_uuid),
                },
            },
            'sodar_uuid': str(self.project.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_project_title_delimiter(self):
        """Test PATCH with category delimiter in project title (should fail)"""
        patch_data = {'title': 'New{}Project'.format(CAT_DELIMITER)}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch_project_owner(self):
        """Test PATCH for updating project owner (should fail)"""
        new_owner = self.make_user('new_owner')
        patch_data = {'owner': str(new_owner.sodar_uuid)}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch_project_move(self):
        """Test PATCH for moving project under different category"""
        self.assertEqual(
            self.project.full_title,
            self.category.title + CAT_DELIMITER + self.project.title,
        )
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(new_category, self.user_owner_cat, self.role_owner)
        patch_data = {'parent': str(new_category.sodar_uuid)}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project.refresh_from_db()
        model_dict = model_to_dict(self.project)
        self.assertEqual(model_dict['parent'], new_category.pk)
        owners = [a.user for a in self.project.get_owners()]
        self.assertIn(self.user_owner_cat, owners)
        self.assertIn(self.user_owner, owners)

        # Assert child project full title update
        self.assertEqual(
            self.project.full_title,
            new_category.title + CAT_DELIMITER + self.project.title,
        )
        self.assertEqual(
            json.loads(response.content)['parent'], str(new_category.sodar_uuid)
        )

    def test_patch_project_move_unallowed(self):
        """Test PATCH for moving project without permissions (should fail)"""
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        new_owner = self.make_user('new_owner')
        self.make_assignment(new_category, new_owner, self.role_owner)
        patch_data = {'parent': str(new_category.sodar_uuid)}
        # Disable superuser status from self.user and perform request
        self.user.is_superuser = False
        self.user.save()
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 403, msg=response.content)

    def test_patch_project_move_root(self):
        """Test PATCH for moving project without permissions (should fail)"""
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        new_owner = self.make_user('new_owner')
        self.make_assignment(new_category, new_owner, self.role_owner)
        patch_data = {'parent': ''}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 200, msg=response.content)

    def test_patch_project_move_root_unallowed(self):
        """Test PATCH for moving project to root without permissions (should fail)"""
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, None
        )
        new_owner = self.make_user('new_owner')
        self.make_assignment(new_category, new_owner, self.role_owner)
        patch_data = {'parent': ''}
        # Disable superuser status from self.user and perform request
        self.user.is_superuser = False
        self.user.save()
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 403, msg=response.content)

    def test_patch_project_move_child(self):
        """Test PATCH for moving category inside its child (should fail)"""
        new_category = self.make_project(
            'NewCategory', PROJECT_TYPE_CATEGORY, self.category
        )
        self.make_assignment(new_category, self.user, self.role_owner)
        patch_data = {'parent': str(new_category.sodar_uuid)}
        response = self.request_knox(
            self.url_cat, method='PATCH', data=patch_data
        )
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch_project_type_change(self):
        """Test PATCH with changed project type (should fail)"""
        patch_data = {'type': PROJECT_TYPE_CATEGORY}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch_project_public(self):
        """Test PATCH with changed public guest access"""
        self.assertEqual(self.project.public_guest_access, False)
        self.assertEqual(self.category.has_public_children, False)
        patch_data = {'public_guest_access': True}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project.refresh_from_db()
        self.category.refresh_from_db()
        self.assertEqual(self.project.public_guest_access, True)
        # Assert the parent category has_public_children is set true
        self.assertEqual(self.category.has_public_children, True)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_patch_project_remote(self):
        """Test PATCH with remote project (should fail)"""
        # Create source site and remote project
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        patch_data = {
            'title': UPDATED_TITLE,
            'description': UPDATED_DESC,
            'readme': UPDATED_README,
        }
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)


class TestProjectDestroyAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectDestroyAPIView"""

    @classmethod
    def _get_delete_tl(cls):
        return TimelineEvent.objects.filter(event_name='project_delete')

    def _get_delete_alerts(self):
        return self.app_alert_model.objects.filter(alert_name='project_delete')

    def setUp(self):
        super().setUp()
        self.app_alert_model = get_backend_api('appalerts_backend').get_model()
        self.url = reverse(
            'projectroles:api_project_destroy',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:api_project_destroy',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_delete(self):
        """Test ProjectDestroyAPIView DELETE"""
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(self._get_delete_tl().count(), 0)
        self.assertEqual(self._get_delete_alerts().count(), 0)
        self.assertEqual(len(mail.outbox), 0)

        response = self.request_knox(self.url, method='DELETE')
        self.assertEqual(response.status_code, 204, msg=response.content)
        self.assertEqual(Project.objects.count(), 1)
        self.assertIsNone(
            Project.objects.filter(sodar_uuid=self.project.sodar_uuid).first(),
            None,
        )
        self.assertEqual(self._get_delete_tl().count(), 1)
        alerts = self._get_delete_alerts()
        self.assertEqual(alerts.count(), 2)
        self.assertEqual(
            sorted([a.user.username for a in alerts]),
            sorted(['user_owner', 'user_owner_cat']),
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_delete_v1_0(self):
        """Test DELETE with API version 1.0 (should fail)"""
        self.assertEqual(Project.objects.count(), 2)
        response = self.request_knox(self.url, method='DELETE', version='1.0')
        self.assertEqual(response.status_code, 406, msg=response.content)
        self.assertEqual(Project.objects.count(), 2)


class TestRoleAssignmentCreateAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for RoleAssignmentCreateAPIView"""

    def setUp(self):
        super().setUp()
        self.assign_user = self.make_user('assign_user')
        self.url = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:api_role_create',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_post_contributor(self):
        """Test RoleAssignmentCreateAPIView POST with contributor role"""
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        post_data = {
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )
        role_as = RoleAssignment.objects.filter(
            project=self.project,
            role=self.role_contributor,
            user=self.assign_user,
        ).first()
        self.assertIsNotNone(role_as)
        expected = {
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
            'sodar_uuid': str(role_as.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_owner(self):
        """Test POST with owner role (should fail)"""
        post_data = {
            'role': PROJECT_ROLE_OWNER,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_post_delegate(self):
        """Test POST with delegate role as owner"""
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        post_data = {
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(
            self.url,
            method='POST',
            data=post_data,
            token=self.get_token(self.user_owner),
        )

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )
        role_as = RoleAssignment.objects.filter(
            project=self.project, role=self.role_delegate, user=self.assign_user
        ).first()
        self.assertIsNotNone(role_as)

    def test_post_delegate_unauthorized(self):
        """Test POST with delegate role without authorization (should fail)"""
        # Create new user and grant delegate role
        new_user = self.make_user('new_user')
        self.make_assignment(self.project, new_user, self.role_contributor)
        new_user_token = self.get_token(new_user)
        post_data = {
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(
            self.url, method='POST', data=post_data, token=new_user_token
        )
        self.assertEqual(response.status_code, 403, msg=response.content)

    def test_post_delegate_limit(self):
        """Test POST with delegate role and limit reached (should fail)"""
        new_user = self.make_user('new_user')
        self.make_assignment(self.project, new_user, self.role_delegate)
        post_data = {
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
        }
        # NOTE: Post as owner
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_post_delegate_limit_inherit(self):
        """Test POST with delegate role and existing role for inherited owner"""
        # Set up category owner
        new_user = self.make_user('new_user')
        self.owner_as_cat.user = new_user

        post_data = {
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
        }
        # NOTE: Post as owner
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )
        role_as = RoleAssignment.objects.filter(
            project=self.project, role=self.role_delegate, user=self.assign_user
        ).first()
        self.assertIsNotNone(role_as)

    def test_post_delegate_category(self):
        """Test POST with non-owner role for category"""
        post_data = {
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(
            self.url_cat, method='POST', data=post_data
        )
        self.assertEqual(response.status_code, 201, msg=response.content)

    def test_post_finder_project(self):
        """Test POST with finder role for project (should fail)"""
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        post_data = {
            'role': PROJECT_ROLE_FINDER,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(
            self.url,
            method='POST',
            data=post_data,
            token=self.get_token(self.user_owner),
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )

    def test_post_finder_category(self):
        """Test POST with finder role for category"""
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 1
        )
        post_data = {
            'role': PROJECT_ROLE_FINDER,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(
            self.url_cat,
            method='POST',
            data=post_data,
            token=self.get_token(self.user_owner_cat),
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        role_as = RoleAssignment.objects.filter(
            project=self.category, role=self.role_finder, user=self.assign_user
        ).first()
        self.assertIsNotNone(role_as)

    def test_post_existing(self):
        """Test POST with role for user with existing role in project"""
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )
        post_data = {
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )
        post_data = {
            'role': PROJECT_ROLE_GUEST,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )

    def test_post_inherited_promote(self):
        """Test POST for user with inherited role"""
        # Create category role for user
        self.make_assignment(self.category, self.assign_user, self.role_guest)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )

        post_data = {
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )
        role_as = RoleAssignment.objects.filter(
            project=self.project,
            role=self.role_contributor,
            user=self.assign_user,
        ).first()
        self.assertIsNotNone(role_as)

    def test_post_inherited_equal(self):
        """Test POST with equal role for user with inherited role"""
        self.make_assignment(
            self.category, self.assign_user, self.role_contributor
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )

        post_data = {
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 2
        )
        role_as = RoleAssignment.objects.filter(
            project=self.project,
            role=self.role_contributor,
            user=self.assign_user,
        ).first()
        self.assertIsNotNone(role_as)

    def test_post_inherited_demote(self):
        """Test POST with demoted role for user with inherited role (should fail)"""
        self.make_assignment(
            self.category, self.assign_user, self.role_delegate
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )

        post_data = {
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.category).count(), 2
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_remote(self):
        """Test POST for role in remote project (should fail)"""
        # Create source site and remote project
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )

        post_data = {
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            RoleAssignment.objects.filter(project=self.project).count(), 1
        )


class TestRoleAssignmentUpdateAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for RoleAssignmentUpdateAPIView"""

    def setUp(self):
        super().setUp()
        self.assign_user = self.make_user('assign_user')
        self.update_as = self.make_assignment(
            self.project, self.assign_user, self.role_contributor
        )
        self.url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': self.update_as.sodar_uuid},
        )

    def test_put(self):
        """Test RoleAssignmentUpdateAPIView PUT"""
        self.assertEqual(RoleAssignment.objects.count(), 3)
        put_data = {
            'role': PROJECT_ROLE_GUEST,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='PUT', data=put_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 3)

        self.update_as.refresh_from_db()
        model_dict = model_to_dict(self.update_as)
        expected = {
            'id': self.update_as.pk,
            'project': self.project.pk,
            'role': self.role_guest.pk,
            'user': self.assign_user.pk,
            'sodar_uuid': self.update_as.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        expected = {
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_GUEST,
            'user': str(self.assign_user.sodar_uuid),
            'sodar_uuid': str(self.update_as.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_put_delegate(self):
        """Test PUT with delegate role assignment"""
        put_data = {
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='PUT', data=put_data)
        self.assertEqual(response.status_code, 200, msg=response.content)

        self.update_as.refresh_from_db()
        model_dict = model_to_dict(self.update_as)
        expected = {
            'id': self.update_as.pk,
            'project': self.project.pk,
            'role': self.role_delegate.pk,
            'user': self.assign_user.pk,
            'sodar_uuid': self.update_as.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)

        expected = {
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
            'sodar_uuid': str(self.update_as.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_put_owner(self):
        """Test PUT with owner role assignment (should fail)"""
        put_data = {
            'role': PROJECT_ROLE_OWNER,
            'user': str(self.assign_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='PUT', data=put_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_put_change_user(self):
        """Test PUT with different user than one in assignment (should fail)"""
        new_user = self.make_user('new_user')
        put_data = {
            'role': PROJECT_ROLE_GUEST,
            'user': str(new_user.sodar_uuid),
        }
        response = self.request_knox(self.url, method='PUT', data=put_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch(self):
        """Test PATCH to update role assignment"""
        self.assertEqual(RoleAssignment.objects.count(), 3)
        patch_data = {'role': PROJECT_ROLE_GUEST}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 3)
        self.update_as.refresh_from_db()
        model_dict = model_to_dict(self.update_as)
        expected = {
            'id': self.update_as.pk,
            'project': self.project.pk,
            'role': self.role_guest.pk,
            'user': self.assign_user.pk,
            'sodar_uuid': self.update_as.sodar_uuid,
        }
        self.assertEqual(model_dict, expected)
        expected = {
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_GUEST,
            'user': str(self.assign_user.sodar_uuid),
            'sodar_uuid': str(self.update_as.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_role_finder_project(self):
        """Test PATCH for finder role in project (should fail)"""
        self.assertEqual(RoleAssignment.objects.count(), 3)
        patch_data = {'role': PROJECT_ROLE_FINDER}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch_role_finder_category(self):
        """Test PATCH for finder role in categody"""
        user_new = self.make_user('user_new')
        new_as = self.make_assignment(self.category, user_new, self.role_finder)
        self.assertEqual(RoleAssignment.objects.count(), 4)
        url = reverse(
            'projectroles:api_role_update',
            kwargs={'roleassignment': new_as.sodar_uuid},
        )
        patch_data = {'role': PROJECT_ROLE_FINDER}
        response = self.request_knox(url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 4)
        new_as.refresh_from_db()
        self.assertEqual(new_as.role, self.role_finder)

    def test_patch_role_inherited_promote(self):
        """Test PATCH with promoted role for inherited user"""
        self.make_assignment(
            self.category, self.assign_user, self.role_contributor
        )
        self.assertEqual(RoleAssignment.objects.count(), 4)
        patch_data = {'role': PROJECT_ROLE_DELEGATE}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 4)
        expected = {
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_DELEGATE,
            'user': str(self.assign_user.sodar_uuid),
            'sodar_uuid': str(self.update_as.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_role_inherited_equal(self):
        """Test PATCH with equal role for inherited user"""
        self.make_assignment(
            self.category, self.assign_user, self.role_contributor
        )
        self.assertEqual(RoleAssignment.objects.count(), 4)
        patch_data = {'role': PROJECT_ROLE_CONTRIBUTOR}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 4)
        expected = {
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'user': str(self.assign_user.sodar_uuid),
            'sodar_uuid': str(self.update_as.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_patch_role_inherited_demote(self):
        """Test PATCH with demoted role for inherited user (should fail)"""
        self.make_assignment(
            self.category, self.assign_user, self.role_contributor
        )
        self.assertEqual(RoleAssignment.objects.count(), 4)
        patch_data = {'role': PROJECT_ROLE_GUEST}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 4)
        self.update_as.refresh_from_db()
        self.assertEqual(self.update_as.role, self.role_contributor)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_patch_role_remote(self):
        """Test PATCH for updating role in remote project (should fail)"""
        # Create source site and remote project
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        patch_data = {'role': PROJECT_ROLE_GUEST}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_patch_user(self):
        """Test PATCH with different user (should fail)"""
        new_user = self.make_user('new_user')
        patch_data = {'user': str(new_user.sodar_uuid)}
        response = self.request_knox(self.url, method='PATCH', data=patch_data)
        self.assertEqual(response.status_code, 400, msg=response.content)


class TestRoleAssignmentDestroyAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for RoleAssignmentDestroyAPIView"""

    def setUp(self):
        super().setUp()
        self.assign_user = self.make_user('assign_user')
        self.update_as = self.make_assignment(
            self.project, self.assign_user, self.role_contributor
        )

    def test_delete(self):
        """Test RoleAssignmentDestroyAPIView DELETE"""
        self.assertEqual(RoleAssignment.objects.count(), 3)
        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': self.update_as.sodar_uuid},
        )
        response = self.request_knox(url, method='DELETE')
        self.assertEqual(response.status_code, 204, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 2)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.assign_user
            ).count(),
            0,
        )

    def test_delete_delegate_unauthorized(self):
        """Test DELETE with delegate role without perms (should fail)"""
        new_user = self.make_user('new_user')
        delegate_as = self.make_assignment(
            self.project, new_user, self.role_delegate
        )
        self.assertEqual(RoleAssignment.objects.count(), 4)
        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': delegate_as.sodar_uuid},
        )
        # NOTE: Perform record as contributor user
        token = self.get_token(self.assign_user)
        response = self.request_knox(url, method='DELETE', token=token)
        self.assertEqual(response.status_code, 403, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 4)

    def test_delete_owner(self):
        """Test DELETE with owner role (should fail)"""
        self.assertEqual(RoleAssignment.objects.count(), 3)
        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        response = self.request_knox(url, method='DELETE')
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 3)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_delete_remote(self):
        """Test DELETE with remote project (should fail)"""
        # Create source site and remote project
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.assertEqual(RoleAssignment.objects.count(), 3)
        url = reverse(
            'projectroles:api_role_destroy',
            kwargs={'roleassignment': self.update_as.sodar_uuid},
        )
        response = self.request_knox(url, method='DELETE')
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(RoleAssignment.objects.count(), 3)


class TestRoleAssignmentOwnerTransferAPIView(
    RemoteSiteMixin, RemoteProjectMixin, ProjectrolesAPIViewTestBase
):
    """Tests for RoleAssignmentOwnerTransferAPIView"""

    def setUp(self):
        super().setUp()
        self.user_guest = self.make_user('user_guest')
        self.guest_as = self.make_assignment(
            self.project, self.user_guest, self.role_guest
        )
        self.user_new = self.make_user('user_new')
        self.url = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_cat = reverse(
            'projectroles:api_role_owner_transfer',
            kwargs={'project': self.category.sodar_uuid},
        )

    def test_post(self):
        """Test RoleAssignmentOwnerTransferAPIView POST"""
        # Assign role to new user
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_new)

    def test_post_category(self):
        """Test POST with category"""
        self.make_assignment(
            self.category, self.user_new, self.role_contributor
        )
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(
            self.url_cat, method='POST', data=post_data
        )
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.category.get_owner().user, self.user_new)

    def test_post_finder_project(self):
        """Test POST with finder role in project (should fail)"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_FINDER,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)

    def test_post_finder_category(self):
        """Test POST with finder role in category"""
        self.make_assignment(
            self.category, self.user_new, self.role_contributor
        )
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_FINDER,
        }
        response = self.request_knox(
            self.url_cat, method='POST', data=post_data
        )
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.category.get_owner().user, self.user_new)

    def test_post_old_inherited_member(self):
        """Test POST to transfer from old owner with inherited non-owner role"""
        self.make_assignment(
            self.category, self.user_owner, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        post_data = {
            'new_owner': self.user_guest.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_guest)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)

    def test_post_old_inherited_member_demote(self):
        """Test POST with demoting inherited non-owner (should fail)"""
        self.make_assignment(
            self.category, self.user_owner, self.role_contributor
        )
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        post_data = {
            'new_owner': self.user_guest.username,
            'old_owner_role': PROJECT_ROLE_GUEST,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        self.assertEqual(
            self.project.get_role(self.user_guest).role, self.role_guest
        )

    def test_post_old_inherited_owner(self):
        """Test POST to transfer from old owner with inherited owner role"""
        self.owner_as_cat.user = self.user_owner
        self.owner_as_cat.save()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        post_data = {
            'new_owner': self.user_guest.username,
            'old_owner_role': PROJECT_ROLE_OWNER,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_guest)
        self.assertIsNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner
            ).first()
        )
        self.assertEqual(
            self.project.get_role(self.user_owner), self.owner_as_cat
        )
        self.assertEqual(self.owner_as.role, self.role_owner)

    def test_post_old_inherited_owner_demote(self):
        """Test POST demoting inherited owner (should fail)"""
        self.owner_as_cat.user = self.user_owner
        self.owner_as_cat.save()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        post_data = {
            'new_owner': self.user_guest.username,
            'old_owner_role': PROJECT_ROLE_DELEGATE,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        self.assertEqual(
            self.project.get_role(self.user_guest).role, self.role_guest
        )

    def test_post_new_inherited_member(self):
        """Test POST for transfer to new owner with inherited non-owner role"""
        self.make_assignment(
            self.category, self.user_new, self.role_contributor
        )
        self.assertEqual(
            self.project.get_owners(inherited_only=True)[0].user,
            self.user_owner_cat,
        )
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)

    def test_post_new_inherited_owner(self):
        """Test POST for transfer to new owner with inherited owner role"""
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        self.assertEqual(
            self.project.get_owners(inherited_only=True)[0].user,
            self.user_owner_cat,
        )
        post_data = {
            'new_owner': self.user_owner_cat.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner_cat)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.project.get_role(self.user_owner), self.owner_as)
        self.assertEqual(self.owner_as.role, self.role_contributor)
        self.assertEqual(
            self.project.get_role(self.user_owner_cat),
            RoleAssignment.objects.get(
                project=self.project,
                user=self.user_owner_cat,
                role=self.role_owner,
            ),
        )

    def test_post_no_roles(self):
        """Test POST to transfer to user with no existing roles (should fail)"""
        # NOTE: No role given to user
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_post_inherit_promote(self):
        """Test post with promoted inherited role for old owner"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        # Set category role for project owner
        self.make_assignment(self.category, self.user_owner, self.role_guest)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.assertEqual(
            self.project.get_role(self.user_owner).role, self.role_contributor
        )

    def test_post_inherit_equal(self):
        """Test POST with equal inherited role for old owner"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        # Set category role for project owner
        self.make_assignment(
            self.category, self.user_owner, self.role_contributor
        )
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.assertEqual(
            self.project.get_role(self.user_owner).role, self.role_contributor
        )

    def test_post_inherit_demote(self):
        """Test POST with demoted role for old owner (should fail)"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        # Set category role for project owner
        self.make_assignment(self.category, self.user_owner, self.role_delegate)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        self.assertEqual(
            self.project.get_role(self.user_new).role, self.role_contributor
        )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_remote(self):
        """Test POST with remote project (should fail)"""
        # Create source site and remote project
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        # Assign role to new user
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)

        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': PROJECT_ROLE_CONTRIBUTOR,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)

    def test_post_no_old_role(self):
        """Test POST with no old user role"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': None,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_new)
        self.assertIsNone(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner
            ).first()
        )

    def test_post_no_old_role_v1_0(self):
        """Test POST with no old user role and v1.0 (should fail)"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': None,
        }
        response = self.request_knox(
            self.url, method='POST', data=post_data, version='1.0'
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)

    def test_post_invalid_role(self):
        """Test POST with invalid old owner role (should fail)"""
        self.make_assignment(self.project, self.user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        post_data = {
            'new_owner': self.user_new.username,
            'old_owner_role': 'INVALID ROLE',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(self.project.get_owner().user, self.user_owner)


class TestProjectInviteListAPIView(
    ProjectInviteMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectInviteListAPIView"""

    def setUp(self):
        super().setUp()
        # Create invites
        self.invite = self.make_invite(
            email=INVITE_USER_EMAIL,
            project=self.project,
            role=self.role_guest,
            issuer=self.user,
            message='',
            secret=build_secret(),
        )
        self.invite2 = self.make_invite(
            email=INVITE_USER2_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
            message=INVITE_MESSAGE,
            secret=build_secret(),
        )
        self.url = reverse(
            'projectroles:api_invite_list',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test ProjectInviteListAPIView GET"""
        response = self.request_knox(self.url, token=self.get_token(self.user))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        expected = [
            {
                'email': INVITE_USER_EMAIL,
                'project': str(self.project.sodar_uuid),
                'role': PROJECT_ROLE_GUEST,
                'issuer': self.get_serialized_user(self.user),
                'date_created': self.get_drf_datetime(self.invite.date_created),
                'date_expire': self.get_drf_datetime(self.invite.date_expire),
                'message': '',
                'sodar_uuid': str(self.invite.sodar_uuid),
            },
            {
                'email': INVITE_USER2_EMAIL,
                'project': str(self.project.sodar_uuid),
                'role': PROJECT_ROLE_CONTRIBUTOR,
                'issuer': self.get_serialized_user(self.user),
                'date_created': self.get_drf_datetime(
                    self.invite2.date_created
                ),
                'date_expire': self.get_drf_datetime(self.invite2.date_expire),
                'message': INVITE_MESSAGE,
                'sodar_uuid': str(self.invite2.sodar_uuid),
            },
        ]
        self.assertEqual(response_data, expected)

    def test_get_inactive(self):
        """Test GET with inactive invite"""
        self.invite.active = False
        self.invite.save()
        response = self.request_knox(self.url, token=self.get_token(self.user))

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        expected = [
            {
                'email': INVITE_USER2_EMAIL,
                'project': str(self.project.sodar_uuid),
                'role': PROJECT_ROLE_CONTRIBUTOR,
                'issuer': self.get_serialized_user(self.user),
                'date_created': self.get_drf_datetime(
                    self.invite2.date_created
                ),
                'date_expire': self.get_drf_datetime(self.invite2.date_expire),
                'message': INVITE_MESSAGE,
                'sodar_uuid': str(self.invite2.sodar_uuid),
            },
        ]
        self.assertEqual(response_data, expected)

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url, token=self.get_token(self.user))
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'count': 2,
            'next': TEST_SERVER_URL + self.url + '?page=2',
            'previous': None,
            'results': [
                {
                    'email': INVITE_USER_EMAIL,
                    'project': str(self.project.sodar_uuid),
                    'role': PROJECT_ROLE_GUEST,
                    'issuer': self.get_serialized_user(self.user),
                    'date_created': self.get_drf_datetime(
                        self.invite.date_created
                    ),
                    'date_expire': self.get_drf_datetime(
                        self.invite.date_expire
                    ),
                    'message': '',
                    'sodar_uuid': str(self.invite.sodar_uuid),
                }
            ],
        }
        self.assertEqual(response_data, expected)


class TestProjectInviteCreateAPIView(
    ProjectInviteMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    ProjectrolesAPIViewTestBase,
):
    """Tests for ProjectInviteCreateAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.post_data = {
            'email': INVITE_USER_EMAIL,
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'message': INVITE_MESSAGE,
        }

    def test_post(self):
        """Test ProjectInviteCreateAPIView POST"""
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 1
        )
        invite = ProjectInvite.objects.first()
        self.assertEqual(invite.email, INVITE_USER_EMAIL)
        self.assertEqual(invite.role, self.role_contributor)
        self.assertEqual(invite.issuer, self.user)
        self.assertEqual(invite.message, INVITE_MESSAGE)

        expected = {
            'email': INVITE_USER_EMAIL,
            'project': str(self.project.sodar_uuid),
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'issuer': self.get_serialized_user(self.user),
            'date_created': self.get_drf_datetime(invite.date_created),
            'date_expire': self.get_drf_datetime(invite.date_expire),
            'message': invite.message,
            'sodar_uuid': str(invite.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_owner(self):
        """Test POST with owner role (should fail)"""
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.post_data['role'] = PROJECT_ROLE_OWNER
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_delegate(self):
        """Test POST with delegate role"""
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.post_data['role'] = PROJECT_ROLE_DELEGATE
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 1
        )
        invite = ProjectInvite.objects.first()
        self.assertEqual(invite.role, self.role_delegate)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_post_delegate_no_perms(self):
        """Test POST for delegate without perms (should fail)"""
        del_user = self.make_user('delegate')
        self.make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.post_data['role'] = PROJECT_ROLE_DELEGATE
        response = self.request_knox(
            self.url,
            method='POST',
            data=self.post_data,
            token=self.get_token(del_user),
        )
        self.assertEqual(response.status_code, 403, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_delegate_limit(self):
        """Test POST for delegate with exceeded limit (should fail)"""
        del_user = self.make_user('delegate')
        self.make_assignment(self.project, del_user, self.role_delegate)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.post_data['role'] = PROJECT_ROLE_DELEGATE
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_invalid_email(self):
        """Test POST with invalid email (should fail)"""
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.post_data['email'] = 'NOT_AN_EMAIL!'
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_existing_user(self):
        """Test POST with existing user (should fail)"""
        user = self.make_user('new_user')
        user.email = INVITE_USER_EMAIL
        user.save()
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_post_parent_invite(self):
        """Test POST with active parent invite (should fail)"""
        self.make_invite(
            email=INVITE_USER_EMAIL,
            project=self.category,
            role=self.role_contributor,
            issuer=self.user,
        )
        self.assertEqual(ProjectInvite.objects.count(), 1)
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(ProjectInvite.objects.count(), 1)

    def test_post_parent_invite_inactive(self):
        """Test POST with inactive parent invite"""
        self.make_invite(
            email=INVITE_USER_EMAIL,
            project=self.category,
            role=self.role_contributor,
            issuer=self.user,
            active=False,
        )
        self.assertEqual(ProjectInvite.objects.count(), 1)
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(ProjectInvite.objects.count(), 2)

    def test_post_parent_invite_expired(self):
        """Test POST with expired parent invite"""
        self.make_invite(
            email=INVITE_USER_EMAIL,
            project=self.category,
            role=self.role_contributor,
            issuer=self.user,
            date_expire=timezone.now() + timezone.timedelta(days=-1),
        )
        self.assertEqual(ProjectInvite.objects.count(), 1)
        response = self.request_knox(
            self.url, method='POST', data=self.post_data
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(ProjectInvite.objects.count(), 2)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_post_remote(self):
        """Test POST with remote project (should fail)"""
        # Set up remote site and project
        source_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=source_site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )

        post_data = {
            'email': INVITE_USER_EMAIL,
            'role': PROJECT_ROLE_CONTRIBUTOR,
            'message': INVITE_MESSAGE,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 0
        )
        self.assertEqual(len(mail.outbox), 0)


class TestProjectInviteRevokeAPIView(
    ProjectInviteMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectInviteRevokeAPIView"""

    def setUp(self):
        super().setUp()
        # Create invite
        self.invite = self.make_invite(
            email=INVITE_USER_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
        )
        self.url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )

    def test_post(self):
        """Test ProjectInviteRevokeAPIView POST"""
        self.assertEqual(self.invite.active, True)
        response = self.request_knox(self.url, method='POST')
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.active, False)

    def test_post_inactive(self):
        """Test POST with inactive invite (should fail)"""
        self.invite.active = False
        self.invite.save()
        response = self.request_knox(self.url, method='POST')
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_post_delegate(self):
        """Test POST for delegate invite with sufficient perms"""
        self.invite.role = self.role_delegate
        self.invite.save()
        response = self.request_knox(self.url, method='POST')
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.active, False)

    def test_post_delegate_no_perms(self):
        """Test POST for delegate invite without perms (should fail)"""
        self.invite.role = self.role_delegate
        self.invite.save()
        delegate = self.make_user('delegate')
        self.make_assignment(self.project, delegate, self.role_delegate)
        response = self.request_knox(
            self.url, method='POST', token=self.get_token(delegate)
        )
        self.assertEqual(response.status_code, 403, msg=response.content)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.active, True)

    def test_post_not_found(self):
        """Test POST with invalid UUID"""
        url = reverse(
            'projectroles:api_invite_revoke',
            kwargs={'projectinvite': INVALID_UUID},
        )
        response = self.request_knox(url, method='POST')
        self.assertEqual(response.status_code, 404)


class TestProjectInviteResendAPIView(
    ProjectInviteMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectInviteResendAPIView"""

    def setUp(self):
        super().setUp()
        # Create invite
        self.invite = self.make_invite(
            email=INVITE_USER_EMAIL,
            project=self.project,
            role=self.role_contributor,
            issuer=self.user,
        )
        self.url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': self.invite.sodar_uuid},
        )

    def test_post(self):
        """Test ProjectInviteResendAPIView POST"""
        self.assertEqual(len(mail.outbox), 0)
        response = self.request_knox(self.url, method='POST')
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_inactive(self):
        """Test POST with inactive invite (should fail)"""
        self.invite.active = False
        self.invite.save()
        response = self.request_knox(self.url, method='POST')
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_delegate(self):
        """Test POST for delegate invite with sufficient perms"""
        self.invite.role = self.role_delegate
        self.invite.save()
        response = self.request_knox(self.url, method='POST')
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(len(mail.outbox), 1)

    def test_post_delegate_no_perms(self):
        """Test POST for delegate invite without perms (should fail)"""
        self.invite.role = self.role_delegate
        self.invite.save()
        delegate = self.make_user('delegate')
        self.make_assignment(self.project, delegate, self.role_delegate)
        response = self.request_knox(
            self.url, method='POST', token=self.get_token(delegate)
        )
        self.assertEqual(response.status_code, 403, msg=response.content)
        self.assertEqual(len(mail.outbox), 0)

    def test_post_invalid_uuid(self):
        """Test POST with invalid UUID"""
        url = reverse(
            'projectroles:api_invite_resend',
            kwargs={'projectinvite': INVALID_UUID},
        )
        response = self.request_knox(url, method='POST')
        self.assertEqual(response.status_code, 404)


class TestProjectSettingRetrievePIView(
    AppSettingMixin, AppSettingInitMixin, ProjectrolesAPIViewTestBase
):
    """Tests for ProjectSettingRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        self.settings = self.init_app_settings()
        self.url = reverse(
            'projectroles:api_project_setting_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get_project(self):
        """Test ProjectSettingRetrieveAPIView GET with PROJECT scope setting"""
        setting_name = 'project_str_setting'
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': str(self.project.sodar_uuid),
            'user': None,
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': self.project_str_setting['value'],
            'user_modifiable': True,
        }
        self.assertEqual(response_data, expected)

    def test_get_project_unset(self):
        """Test GET with unset PROJECT setting (should return default)"""
        setting_name = 'project_str_setting'
        default_value = app_settings.get_default(EX_APP_NAME, setting_name)
        q_kwargs = {
            'app_plugin__name': EX_APP_NAME,
            'name': setting_name,
            'project': self.project,
        }
        AppSetting.objects.get(**q_kwargs).delete()
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': str(self.project.sodar_uuid),
            'user': None,
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': default_value,
            'user_modifiable': True,
        }
        self.assertEqual(response_data, expected)
        self.assertIsInstance(AppSetting.objects.get(**q_kwargs), AppSetting)

    def test_get_project_user(self):
        """Test GET with PROJECT_USER scope setting"""
        setting_name = 'project_user_str_setting'
        get_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'user': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, data=get_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': str(self.project.sodar_uuid),
            'user': self.get_serialized_user(self.user),
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': self.project_user_str_setting['value'],
            'user_modifiable': True,
        }
        self.assertEqual(response_data, expected)

    def test_get_project_user_unset(self):
        """Test GET with unset PROJECT_USER setting"""
        setting_name = 'project_user_str_setting'
        default_value = app_settings.get_default(EX_APP_NAME, setting_name)
        q_kwargs = {
            'app_plugin__name': EX_APP_NAME,
            'name': setting_name,
            'project': self.project,
            'user': self.user,
        }
        AppSetting.objects.get(**q_kwargs).delete()
        get_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'user': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, data=get_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': str(self.project.sodar_uuid),
            'user': self.get_serialized_user(self.user),
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': default_value,
            'user_modifiable': False,
        }
        self.assertEqual(response_data, expected)
        self.assertIsInstance(AppSetting.objects.get(**q_kwargs), AppSetting)

    def test_get_project_user_no_user(self):
        """Test GET with PROJECT_USER setting and no user (should fail)"""
        setting_name = 'project_user_str_setting'
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_get_json(self):
        """Test GET with JSON app setting"""
        setting_name = 'project_json_setting'
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': str(self.project.sodar_uuid),
            'user': None,
            'name': setting_name,
            'type': APP_SETTING_TYPE_JSON,
            'value': self.project_json_setting['value'],
            'user_modifiable': True,
        }
        self.assertEqual(response_data, expected)

    def test_get_non_modifiable(self):
        """Test GET with non-modifiable app setting"""
        setting_name = 'project_hidden_setting'
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': str(self.project.sodar_uuid),
            'user': None,
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': '',
            'user_modifiable': False,
        }
        self.assertEqual(response_data, expected)

    def test_get_invalid_app_name(self):
        """Test GET with invalid app name (should fail)"""
        setting_name = 'project_str_setting'
        get_data = {
            'plugin_name': 'NON-EXISTING-APP',
            'setting_name': setting_name,
        }
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_get_invalid_scope(self):
        """Test GET with invalid scope (should fail)"""
        setting_name = 'user_str_setting'
        get_data = {
            'setting_name': setting_name,
            'user': str(self.user.sodar_uuid),
        }
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 400, msg=response.content)


class TestProjectSettingSetAPIView(ProjectrolesAPIViewTestBase):
    """Tests for ProjectSettingSetAPIView"""

    def setUp(self):
        super().setUp()
        # Set project owner token as default token
        self.knox_token = self.get_token(self.user_owner)
        self.url = reverse(
            'projectroles:api_project_setting_set',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_post_project(self):
        """Test TestProjectSettingSetAPIView POST with PROJECT scope setting"""
        self.assertEqual(AppSetting.objects.count(), 0)
        self.assertIsNone(
            TimelineEvent.objects.filter(
                event_name='app_setting_set_api'
            ).first()
        )
        setting_name = 'project_str_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 1)
        obj = AppSetting.objects.get(name=setting_name, project=self.project)
        self.assertEqual(obj.get_value(), 'value')
        tl_event = TimelineEvent.objects.filter(
            event_name='app_setting_set_api'
        ).first()
        self.assertIsNotNone(tl_event)
        self.assertEqual(tl_event.classified, True)
        self.assertEqual(tl_event.extra_data, {'value': 'value'})

    def test_post_project_user(self):
        """Test POST with PROJECT_USER scope"""
        self.assertEqual(AppSetting.objects.count(), 0)
        setting_name = 'project_user_str_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': 'value',
            'user': str(self.user_owner.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 1)
        obj = AppSetting.objects.get(name=setting_name, project=self.project)
        self.assertEqual(obj.get_value(), 'value')

    def test_post_project_no_user(self):
        """Test setting PROJECT_USER setting with no user (should fail)"""
        setting_name = 'project_user_str_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_non_modifiable(self):
        """Test POST with non-modifiable app setting (should fail)"""
        setting_name = 'project_hidden_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 403, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_invalid_app_name(self):
        """Test POST with invalid app name (should fail)"""
        setting_name = 'project_str_setting'
        post_data = {
            'plugin_name': 'NON-EXISTING-APP',
            'setting_name': setting_name,
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_invalid_scope(self):
        """Test POST with invalid scope (should fail)"""
        setting_name = 'user_str_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_invalid_project_type(self):
        """Test POST with unaccepted project type (should fail)"""
        setting_name = 'category_bool_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': True,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_no_value(self):
        """Test POST without value (should fail)"""
        self.assertEqual(AppSetting.objects.count(), 0)
        setting_name = 'project_str_setting'
        post_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_integer(self):
        """Test POST with integer value"""
        setting_name = 'project_int_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': '170',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        obj = AppSetting.objects.get(name=setting_name, project=self.project)
        self.assertEqual(obj.get_value(), 170)

    def test_post_boolean(self):
        """Test POST with boolean value"""
        setting_name = 'project_bool_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': True,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        obj = AppSetting.objects.get(name=setting_name, project=self.project)
        self.assertEqual(obj.get_value(), True)

    def test_post_json(self):
        """Test POST with JSON value"""
        setting_name = 'project_json_setting'
        value = {'key': 'value'}
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': value,
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        obj = AppSetting.objects.get(name=setting_name, project=self.project)
        self.assertEqual(obj.get_value(), value)


class TestUserSettingRetrievePIView(
    AppSettingMixin, AppSettingInitMixin, ProjectrolesAPIViewTestBase
):
    """Tests for UserSettingRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        self.settings = self.init_app_settings()
        self.url = reverse('projectroles:api_user_setting_retrieve')

    def test_get(self):
        """Test UserSettingRetrieveAPIView GET"""
        setting_name = 'user_str_setting'
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': None,
            'user': self.get_serialized_user(self.user),
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': self.user_str_setting['value'],
            'user_modifiable': True,
        }
        self.assertEqual(response_data, expected)

    def test_get_unset(self):
        """Test GET with unset setting (should return default)"""
        setting_name = 'user_str_setting'
        default_value = app_settings.get_default(EX_APP_NAME, setting_name)
        q_kwargs = {
            'app_plugin__name': EX_APP_NAME,
            'name': setting_name,
            'user': self.user,
        }
        AppSetting.objects.get(**q_kwargs).delete()
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': None,
            'user': self.get_serialized_user(self.user),
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': default_value,
            'user_modifiable': True,
        }
        self.assertEqual(response_data, expected)
        self.assertIsInstance(AppSetting.objects.get(**q_kwargs), AppSetting)

    def test_get_non_modifiable(self):
        """Test GET with non-modifiable USER app setting"""
        setting_name = 'user_hidden_setting'
        get_data = {'plugin_name': EX_APP_NAME, 'setting_name': setting_name}
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 200, msg=response.content)
        response_data = json.loads(response.content)
        expected = {
            'plugin_name': EX_APP_NAME,
            'project': None,
            'user': self.get_serialized_user(self.user),
            'name': setting_name,
            'type': APP_SETTING_TYPE_STRING,
            'value': '',
            'user_modifiable': False,
        }
        self.assertEqual(response_data, expected)

    def test_get_invalid_app_name(self):
        """Test GET with invalid app name (should fail)"""
        get_data = {
            'plugin_name': 'NON-EXISTING-APP',
            'setting_name': 'user_str_setting',
        }
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 400, msg=response.content)

    def test_get_invalid_scope(self):
        """Test GET with invalid scope (should fail)"""
        get_data = {
            'setting_name': 'project_str_setting',
            'project': str(self.project.sodar_uuid),
        }
        response = self.request_knox(self.url, data=get_data)
        self.assertEqual(response.status_code, 400, msg=response.content)


class TestUserSettingSetAPIView(ProjectrolesAPIViewTestBase):
    """Tests for UserSettingSetAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse('projectroles:api_user_setting_set')

    def test_post(self):
        """Test UserSettingSetAPIView POST"""
        self.assertEqual(AppSetting.objects.count(), 0)
        self.assertIsNone(
            TimelineEvent.objects.filter(
                event_name='app_setting_set_api'
            ).first()
        )
        setting_name = 'user_str_setting'
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': setting_name,
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 1)
        obj = AppSetting.objects.get(name=setting_name, user=self.user)
        self.assertEqual(obj.get_value(), 'value')
        self.assertIsNone(
            TimelineEvent.objects.filter(
                event_name='app_setting_set_api'
            ).first()
        )

    def test_post_invalid_app_name(self):
        """Test POST with invalid app name (should fail)"""
        post_data = {
            'plugin_name': 'NON-EXISTING-APP',
            'setting_name': 'user_str_setting',
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_invalid_scope_project(self):
        """Test POST with PROJECT scope (should fail)"""
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': 'project_str_setting',
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_invalid_scope_project_user(self):
        """Test POST with PROJECT_USER scope (should fail)"""
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': 'project_user_str_setting',
            'value': 'value',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_post_no_value(self):
        """Test POST without value (should fail)"""
        self.assertEqual(AppSetting.objects.count(), 0)
        post_data = {
            'plugin_name': EX_APP_NAME,
            'setting_name': 'user_str_setting',
        }
        response = self.request_knox(self.url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(AppSetting.objects.count(), 0)


@override_settings(AUTH_LDAP_USERNAME_DOMAIN=LDAP_DOMAIN)
class TestUserListAPIView(ProjectrolesAPIViewTestBase):
    """Tests for UserListAPIView"""

    def setUp(self):
        super().setUp()
        # Create additional users
        self.user_ldap = self.make_user('user_ldap@' + LDAP_DOMAIN)
        # TODO: Add OIDC user to tests
        self.url = reverse('projectroles:api_user_list')

    def test_get(self):
        """Test UserListAPIView GET as regular user"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_ldap)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)  # System users not returned
        expected = [self.get_serialized_user(self.user_ldap)]
        self.assertEqual(response_data, expected)

    def test_get_superuser(self):
        """Test GET as superuser"""
        response = self.request_knox(self.url)  # Default token is for superuser
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 4)
        expected = [
            self.get_serialized_user(self.user),
            self.get_serialized_user(self.user_owner_cat),
            self.get_serialized_user(self.user_owner),
            self.get_serialized_user(self.user_ldap),
        ]
        self.assertEqual(response_data, expected)

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'count': 4,
            'next': TEST_SERVER_URL + self.url + '?page=2',
            'previous': None,
            'results': [self.get_serialized_user(self.user)],
        }
        self.assertEqual(response_data, expected)

    def test_get_include_system_users(self):
        """Test GET with include_system_users=True"""
        response = self.request_knox(
            self.url + '?include_system_users=1',
            token=self.get_token(self.user_ldap),
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 4)
        expected = [
            self.get_serialized_user(self.user),
            self.get_serialized_user(self.user_owner_cat),
            self.get_serialized_user(self.user_owner),
            self.get_serialized_user(self.user_ldap),
        ]
        self.assertEqual(response_data, expected)

    def test_get_include_system_users_v1_0(self):
        """Test GET with include_system_users=True and version 1.0"""
        response = self.request_knox(
            self.url + '?include_system_users=1',
            token=self.get_token(self.user_ldap),
            version='1.0',
        )
        self.assertEqual(response.status_code, 406)


class TestUserRetrieveAPIView(
    SODARUserAdditionalEmailMixin, ProjectrolesAPIViewTestBase
):
    """Tests for UserRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        # Create additional user
        self.user_ldap = self.make_user('user_ldap@' + LDAP_DOMAIN)
        group, _ = Group.objects.get_or_create(name=LDAP_DOMAIN.lower())
        group.user_set.add(self.user_ldap)
        self.url = reverse(
            'projectroles:api_user_retrieve',
            kwargs={'user': self.user_ldap.sodar_uuid},
        )

    def test_get(self):
        """Test UserRetrieveAPIView GET"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'username': self.user_ldap.username,
            'name': self.user_ldap.name,
            'email': self.user_ldap.email,
            'additional_emails': [],
            'is_superuser': False,
            'auth_type': AUTH_TYPE_LDAP,
            'sodar_uuid': str(self.user_ldap.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_additional_email(self):
        """Test GET with additional email"""
        self.make_email(self.user_ldap, ADD_EMAIL)
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'username': self.user_ldap.username,
            'name': self.user_ldap.name,
            'email': self.user_ldap.email,
            'additional_emails': [ADD_EMAIL],
            'is_superuser': False,
            'auth_type': AUTH_TYPE_LDAP,
            'sodar_uuid': str(self.user_ldap.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        url = reverse(
            'projectroles:api_user_retrieve', kwargs={'user': INVALID_UUID}
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 404)

    def test_get_v1_0(self):
        """Test GET with version 1.0"""
        response = self.request_knox(self.url, version='1.0')
        self.assertEqual(response.status_code, 406)


class TestCurrentUserRetrieveAPIView(
    SODARUserAdditionalEmailMixin, ProjectrolesAPIViewTestBase
):
    """Tests for CurrentUserRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        self.user_ldap = self.make_user('user_ldap@' + LDAP_DOMAIN)
        group, _ = Group.objects.get_or_create(name=LDAP_DOMAIN.lower())
        group.user_set.add(self.user_ldap)
        self.url = reverse('projectroles:api_user_current')

    def test_get(self):
        """Test CurrentUserRetrieveAPIView GET as LDAP user"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_ldap)
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'username': self.user_ldap.username,
            'name': self.user_ldap.name,
            'email': self.user_ldap.email,
            'additional_emails': [],
            'is_superuser': False,
            'auth_type': AUTH_TYPE_LDAP,
            'sodar_uuid': str(self.user_ldap.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_superuser(self):
        """Test GET as superuser"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        expected = {
            'username': self.user.username,
            'name': self.user.name,
            'email': self.user.email,
            'additional_emails': [],
            'is_superuser': True,
            'auth_type': AUTH_TYPE_LOCAL,
            'sodar_uuid': str(self.user.sodar_uuid),
        }
        self.assertEqual(response_data, expected)

    def test_get_v1_0(self):
        """Test GET with version 1.0"""
        response = self.request_knox(
            self.url, token=self.get_token(self.user_ldap), version='1.0'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertNotIn('auth_type', response_data)


class TestAPIVersioning(ProjectrolesAPIViewTestBase):
    """Tests for REST API view versioning using ProjectRetrieveAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_api_versioning(self):
        """Test projectroles API with correct version headers"""
        response = self.request_knox(
            self.url,
            media_type=views_api.PROJECTROLES_API_MEDIA_TYPE,
            version=views_api.PROJECTROLES_API_DEFAULT_VERSION,
        )
        self.assertEqual(response.status_code, 200)

    def test_api_versioning_legacy(self):
        """Test projectroles API with legacy version (should fail)"""
        response = self.request_knox(
            self.url,
            media_type=CORE_API_MEDIA_TYPE_LEGACY,
            version=CORE_API_DEFAULT_VERSION_LEGACY,
        )
        self.assertEqual(response.status_code, 406)

    def test_api_versioning_invalid_version(self):
        """Test projectroles API with unsupported version (should fail)"""
        response = self.request_knox(
            self.url,
            media_type=views_api.PROJECTROLES_API_MEDIA_TYPE,
            version=CORE_API_VERSION_INVALID,
        )
        self.assertEqual(response.status_code, 406)

    def test_api_versioning_invalid_media_type(self):
        """Test projectroles API with unsupported media type (should fail)"""
        response = self.request_knox(
            self.url,
            media_type=CORE_API_MEDIA_TYPE_INVALID,
            version=CORE_API_DEFAULT_VERSION_LEGACY,
        )
        self.assertEqual(response.status_code, 406)


# TODO: To be updated once the legacy API view is redone for SODAR Core v1.0
class TestRemoteProjectGetAPIView(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    SODARAPIViewTestMixin,
    ViewTestBase,
):
    """Tests for remote project getting API view"""

    media_type = views_api.SYNC_API_MEDIA_TYPE
    api_version = views_api.SYNC_API_DEFAULT_VERSION

    def setUp(self):
        super().setUp()
        # Set up projects
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.project_owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )

        # Create target site
        self.target_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_TARGET,
            description=REMOTE_SITE_DESC,
            secret=REMOTE_SITE_SECRET,
        )
        # Create remote project
        self.remote_project = self.make_remote_project(
            site=self.target_site,
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
        )
        self.remote_api = RemoteProjectAPI()

    def test_get(self):
        """Test retrieving project data to target site"""
        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            **self.get_accept_header()
        )
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.content.decode('utf-8'))
        expected = self.remote_api.get_source_data(self.target_site)
        self.assertEqual(response_dict, expected)

    def test_get_invalid_secret(self):
        """Test retrieving project data with invalid secret (should fail)"""
        response = self.client.get(
            reverse(
                'projectroles:api_remote_get', kwargs={'secret': build_secret()}
            ),
            **self.get_accept_header()
        )
        self.assertEqual(response.status_code, 401)

    # TODO: Update test once we have a supported legacy version for this API
    '''
    def test_get_legacy_version(self):
        """Test retrieving project data with legacy target site version"""
        # See issue #1355
        set_star = self.make_setting(
            plugin_name='projectroles',
            name='project_star',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=self.user,
        )
        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            **self.get_accept_header(version='0.13.2')
        )
        self.assertEqual(response.status_code, 200)
        response_dict = json.loads(response.content.decode('utf-8'))
        expected = self.remote_api.get_source_data(
            self.target_site, req_version='0.13.2'
        )
        self.assertEqual(response_dict, expected)
        # Assert user_name is not present in PROJECT_USER setting
        set_data = response_dict['app_settings'][str(set_star.sodar_uuid)]
        self.assertNotIn('user_name', set_data)
    '''

    def test_get_unsupported_version(self):
        """Test retrieving project data with legacy target site version"""
        # See issue #1355
        response = self.client.get(
            reverse(
                'projectroles:api_remote_get',
                kwargs={'secret': REMOTE_SITE_SECRET},
            ),
            **self.get_accept_header(version='0.12.0')
        )
        self.assertEqual(response.status_code, 406)


# IP Allowing Tests ------------------------------------------------------------


class TestIPAllowing(AppSettingMixin, ProjectrolesAPIViewTestBase):
    """Tests for IP allowing settings using ProjectRetrieveAPIView"""

    def _setup_ip_allowing(self, ip_list, role_suffix):
        """Setup users and roles for IP allowing test"""
        # Create new user
        user = self.make_user(role_suffix)
        # Set user access
        if role_suffix == 'owner':
            self.owner_as.user = user
            self.owner_as.save()
            # user_as = self.owner_as
            self.owner_as_cat.user = user
            self.owner_as_cat.save()
        else:
            self.make_assignment(
                self.project, user, getattr(self, 'role_' + role_suffix)
            )
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
            name='ip_allowlist',
            setting_type=APP_SETTING_TYPE_JSON,
            value=None,
            value_json=ip_list,
            project=self.project,
        )
        return user  # , user_as, self.cat_owner_as

    def _get_project_ip_allowing(
        self, username, http_attribute, ip_list, blocked=None
    ):
        """Helper for IP allowing tests"""
        if blocked is None:
            raise Exception('Please set "blocked" argument (True/False)')
        user = self._setup_ip_allowing(ip_list, username)
        url = reverse(
            'projectroles:api_project_retrieve',
            kwargs={'project': self.project.sodar_uuid},
        )
        header = {http_attribute: '192.168.1.1'}
        response = self.request_knox(
            url, token=self.get_token(user), header=header
        )
        if blocked:
            self.assertEqual(response.status_code, 403)
        else:
            self.assertEqual(response.status_code, 200)

    def test_http_x_forwarded_for_block_all_owner(self):
        self._get_project_ip_allowing(
            'owner', 'HTTP_X_FORWARDED_FOR', [], blocked=False
        )

    def test_http_x_forwarded_for_allow_ip_owner(self):
        self._get_project_ip_allowing(
            'owner', 'HTTP_X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_http_x_forwarded_for_block_all_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'HTTP_X_FORWARDED_FOR', [], blocked=False
        )

    def test_http_x_forwarded_for_allow_ip_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'HTTP_X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_http_x_forwarded_for_block_all_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'HTTP_X_FORWARDED_FOR', [], blocked=True
        )

    def test_http_x_forwarded_for_allow_ip_contributor(self):
        self._get_project_ip_allowing(
            'contributor',
            'HTTP_X_FORWARDED_FOR',
            ['192.168.1.1'],
            blocked=False,
        )

    def test_http_x_forwarded_for_block_all_guest(self):
        self._get_project_ip_allowing(
            'guest', 'HTTP_X_FORWARDED_FOR', [], blocked=True
        )

    def test_http_x_forwarded_for_allow_ip_guest(self):
        self._get_project_ip_allowing(
            'guest', 'HTTP_X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_x_forwarded_for_block_all_owner(self):
        self._get_project_ip_allowing(
            'owner', 'X_FORWARDED_FOR', [], blocked=False
        )

    def test_x_forwarded_for_allow_ip_owner(self):
        self._get_project_ip_allowing(
            'owner', 'X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_x_forwarded_for_block_all_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'X_FORWARDED_FOR', [], blocked=False
        )

    def test_x_forwarded_for_allow_ip_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_x_forwarded_for_block_all_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'X_FORWARDED_FOR', [], blocked=True
        )

    def test_forwarded_for_allow_ip_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_forwarded_for_block_all_guest(self):
        self._get_project_ip_allowing(
            'guest', 'X_FORWARDED_FOR', [], blocked=True
        )

    def test_forwarded_for_allow_ip_guest(self):
        self._get_project_ip_allowing(
            'guest', 'X_FORWARDED_FOR', ['192.168.1.1'], blocked=False
        )

    def test_forwarded_block_all_owner(self):
        self._get_project_ip_allowing('owner', 'FORWARDED', [], blocked=False)

    def test_forwarded_allow_ip_owner(self):
        self._get_project_ip_allowing(
            'owner', 'FORWARDED', ['192.168.1.1'], blocked=False
        )

    def test_forwarded_block_all_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'FORWARDED', [], blocked=False
        )

    def test_forwarded_allow_ip_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'FORWARDED', ['192.168.1.1'], blocked=False
        )

    def test_forwarded_block_all_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'FORWARDED', [], blocked=True
        )

    def test_forwarded_allow_ip_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'FORWARDED', ['192.168.1.1'], blocked=False
        )

    def test_forwarded_block_all_guest(self):
        self._get_project_ip_allowing('guest', 'FORWARDED', [], blocked=True)

    def test_forwarded_allow_ip_guest(self):
        self._get_project_ip_allowing(
            'guest', 'FORWARDED', ['192.168.1.1'], blocked=False
        )

    def test_remote_addr_block_all_owner(self):
        self._get_project_ip_allowing('owner', 'REMOTE_ADDR', [], blocked=False)

    def test_remote_addr_allow_ip_owner(self):
        self._get_project_ip_allowing(
            'owner', 'REMOTE_ADDR', ['192.168.1.1'], blocked=False
        )

    def test_remote_addr_block_all_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'REMOTE_ADDR', [], blocked=False
        )

    def test_remote_addr_allow_ip_delegate(self):
        self._get_project_ip_allowing(
            'delegate', 'REMOTE_ADDR', ['192.168.1.1'], blocked=False
        )

    def test_remote_addr_block_all_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'REMOTE_ADDR', [], blocked=True
        )

    def test_remote_addr_allow_ip_contributor(self):
        self._get_project_ip_allowing(
            'contributor', 'REMOTE_ADDR', ['192.168.1.1'], blocked=False
        )

    def test_remote_addr_block_all_guest(self):
        self._get_project_ip_allowing('guest', 'REMOTE_ADDR', [], blocked=True)

    def test_remote_addr_allow_ip_guest(self):
        self._get_project_ip_allowing(
            'guest', 'REMOTE_ADDR', ['192.168.1.1'], blocked=False
        )

    def test_remote_addr_allow_network_guest(self):
        self._get_project_ip_allowing(
            'guest', 'REMOTE_ADDR', ['192.168.1.0/24'], blocked=False
        )

    def test_remote_addr_block_not_in_allowlist_ip_guest(self):
        self._get_project_ip_allowing(
            'guest', 'REMOTE_ADDR', ['192.168.1.2'], blocked=True
        )

    def test_remote_addr_block_not_in_allowlist_network_guest(self):
        self._get_project_ip_allowing(
            'guest', 'REMOTE_ADDR', ['192.168.2.0/24'], blocked=True
        )
