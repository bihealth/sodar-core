"""Tests for REST API views in the sodarcache app"""

import json

from django.conf import settings
from django.forms.models import model_to_dict
from django.test import override_settings
from django.urls import reverse

from test_plus.test import APITestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)
from projectroles.tests.test_views_api import SODARAPIViewTestMixin

from sodarcache.models import JSONCacheItem
from sodarcache.views_api import (
    SODARCACHE_API_MEDIA_TYPE,
    SODARCACHE_API_DEFAULT_VERSION,
)


plugin_api = PluginAPI()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
TEST_APP_NAME = 'example_project_app'
ITEM_NAME = 'test_item'
DATA_KEY = 'test_key'
DATA_VAL = 'test_val'
DATA_VAL_UPDATED = 'test_val_updated'
BACKEND_PLUGINS_NO_CACHE = settings.ENABLED_BACKEND_PLUGINS.copy()
BACKEND_PLUGINS_NO_CACHE.remove('sodar_cache')


class SodarcacheAPIViewTestBase(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    SODARAPIViewTestMixin,
    APITestCase,
):
    """Base class for sodarcache REST API view testing"""

    media_type = SODARCACHE_API_MEDIA_TYPE
    api_version = SODARCACHE_API_DEFAULT_VERSION

    def setUp(self):
        super().setUp()
        # Get cache backend
        self.cache_backend = plugin_api.get_backend_api('sodar_cache')
        # Init roles
        self.init_roles()
        # Init users
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.user_owner = self.make_user('owner')
        # Init project
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Init cache item
        self.item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name=ITEM_NAME,
            data={DATA_KEY: DATA_VAL},
        )
        # Get knox token for self.user
        self.knox_token = self.get_token(self.user)


class TestCacheItemRetrieveAPIView(SodarcacheAPIViewTestBase):
    """Tests for CacheItemRetrieveAPIView"""

    def test_get(self):
        """Test CacheItemRetrieveAPIView GET"""
        url = reverse(
            'sodarcache:api_retrieve',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200)
        expected = {
            'project': str(self.project.sodar_uuid),
            'app_name': TEST_APP_NAME,
            'name': ITEM_NAME,
            'user': str(self.user_owner.sodar_uuid),
            'data': {DATA_KEY: DATA_VAL},
            'date_modified': self.get_drf_datetime(self.item.date_modified),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_get_no_user(self):
        """Test GET with no user for item"""
        self.item.user = None
        self.item.save()
        url = reverse(
            'sodarcache:api_retrieve',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)['user'], None)

    def test_get_no_item(self):
        """Test GET with non-existing item"""
        url = reverse(
            'sodarcache:api_retrieve',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': 'INVALID_ITEM_NAME',
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 404)

    def test_get_invalid_app_name(self):
        """Test GET with invalid app name"""
        url = reverse(
            'sodarcache:api_retrieve',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': 'INVALID_APP_NAME',
                'item_name': ITEM_NAME,
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 400)

    @override_settings(ENABLED_BACKEND_PLUGINS=BACKEND_PLUGINS_NO_CACHE)
    def test_get_backend_disabled(self):
        """Test GET with disabled sodarcache backend"""
        url = reverse(
            'sodarcache:api_retrieve',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 503)


class TestCacheItemDateRetrieveAPIView(SodarcacheAPIViewTestBase):
    """Tests for CacheItemDateRetrieveAPIView"""

    def test_get(self):
        """Test CacheItemDateRetrieveAPIView GET"""
        url = reverse(
            'sodarcache:api_retrieve_date',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        with self.login(self.user):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        expected = self.cache_backend.get_update_time(
            app_name=TEST_APP_NAME, name=ITEM_NAME
        )
        self.assertEqual(response.data['update_time'], expected)

    def test_get_no_item(self):
        """Test GET with non-existing item"""
        url = reverse(
            'sodarcache:api_retrieve_date',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': 'INVALID_ITEM_NAME',
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 404)

    def test_get_invalid_app_name(self):
        """Test GET with invalid app name"""
        url = reverse(
            'sodarcache:api_retrieve_date',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': 'INVALID_APP_NAME',
                'item_name': ITEM_NAME,
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 400)

    @override_settings(ENABLED_BACKEND_PLUGINS=BACKEND_PLUGINS_NO_CACHE)
    def test_get_backend_disabled(self):
        """Test GET with disabled sodarcache backend"""
        url = reverse(
            'sodarcache:api_retrieve_date',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 503)


class TestCacheItemSetAPIView(SodarcacheAPIViewTestBase):
    """Tests for CacheItemSetAPIView"""

    def test_post_create(self):
        """Test CacheItemSetAPIView POST to create item"""
        url = reverse(
            'sodarcache:api_set',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': 'new_test_item',
            },
        )
        post_data = {'data': json.dumps({DATA_KEY: DATA_VAL})}
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        response = self.request_knox(url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'detail': 'ok'})
        self.assertEqual(JSONCacheItem.objects.all().count(), 2)
        item = JSONCacheItem.objects.get(name='new_test_item')
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'user': self.user.pk,
            'name': 'new_test_item',
            'data': json.dumps({DATA_KEY: DATA_VAL}),
            'sodar_uuid': item.sodar_uuid,
        }
        model_dict = model_to_dict(item)
        self.assertEqual(model_dict, expected)

    def test_post_update(self):
        """Test POST to update item"""
        url = reverse(
            'sodarcache:api_set',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        post_data = {'data': json.dumps({DATA_KEY: DATA_VAL_UPDATED})}
        response = self.request_knox(url, method='POST', data=post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'detail': 'ok'})
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        item = JSONCacheItem.objects.get(name=ITEM_NAME)
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'user': self.user.pk,
            'name': ITEM_NAME,
            'data': json.dumps({DATA_KEY: DATA_VAL_UPDATED}),
            'sodar_uuid': item.sodar_uuid,
        }
        model_dict = model_to_dict(item)
        self.assertEqual(model_dict, expected)

    @override_settings(ENABLED_BACKEND_PLUGINS=BACKEND_PLUGINS_NO_CACHE)
    def test_post_backend_disabled(self):
        """Test POST with disabled sodarcache backend"""
        url = reverse(
            'sodarcache:api_set',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        post_data = {'data': json.dumps({DATA_KEY: DATA_VAL_UPDATED})}
        response = self.request_knox(url, method='POST', data=post_data)
        self.assertEqual(response.status_code, 503)
