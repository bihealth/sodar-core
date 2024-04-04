"""Tests for API views in the sodarcache app"""

import json

from django.urls import reverse
from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api

from sodarcache.models import JSONCacheItem
from sodarcache.tests.test_models import (
    JSONCacheItemTestBase,
    JSONCacheItemMixin,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
TEST_APP_NAME = 'sodarcache'
ITEM_NAME = 'test_item'


class SODARCacheViewTestBase(JSONCacheItemMixin, JSONCacheItemTestBase):
    """Base class for sodarcache view testing"""

    def setUp(self):
        super().setUp()
        self.cache_backend = get_backend_api('sodar_cache')
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        # Init project
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Init cache item
        self.item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name=ITEM_NAME,
            data={'test_key': 'test_val'},
        )


class TestSODARCacheGetAPIView(SODARCacheViewTestBase):
    """Tests for SODARCacheGetAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'sodarcache:cache_get',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test SODARCacheGetAPIView GET"""
        values = {'app_name': TEST_APP_NAME, 'name': ITEM_NAME}
        with self.login(self.user):
            response = self.client.get(self.url, values)
        expected = {
            'project_uuid': str(self.project.sodar_uuid),
            'user_uuid': str(self.user_owner.sodar_uuid),
            'name': ITEM_NAME,
            'data': {'test_key': 'test_val'},
            'sodar_uuid': str(self.item.sodar_uuid),
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)

    def test_get_not_found(self):
        """Test GET with a nonexistent item"""
        values = {'app_name': TEST_APP_NAME, 'name': 'not_test_item'}
        with self.login(self.user):
            response = self.client.get(self.url, values)
        self.assertEqual(response.status_code, 404)


class TestSODARCacheSetAPIView(SODARCacheViewTestBase):
    """Tests for SODARCacheSetAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'sodarcache:cache_set',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_post_create(self):
        """Test SODARCacheSetAPIView POST to create cache item"""
        values = {
            'app_name': TEST_APP_NAME,
            'name': 'new_test_item',
            'data': json.dumps({'test_key': 'test_val'}),
        }
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(JSONCacheItem.objects.all().count(), 2)
        item = JSONCacheItem.objects.get(name='new_test_item')
        self.assertIsNotNone(item)
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'user': self.user.pk,
            'name': 'new_test_item',
            'data': json.dumps({'test_key': 'test_val'}),
            'sodar_uuid': item.sodar_uuid,
        }
        model_dict = model_to_dict(item)
        self.assertEqual(model_dict, expected)

    def test_post_update(self):
        """Test POST to update cache item"""
        values = {
            'app_name': TEST_APP_NAME,
            'name': ITEM_NAME,
            'data': json.dumps({'test_key': 'test_val_updated'}),
        }
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url, values)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        item = JSONCacheItem.objects.get(name=ITEM_NAME)
        self.assertIsNotNone(item)
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': TEST_APP_NAME,
            'user': self.user.pk,
            'name': ITEM_NAME,
            'data': json.dumps({'test_key': 'test_val_updated'}),
            'sodar_uuid': item.sodar_uuid,
        }
        model_dict = model_to_dict(item)
        self.assertEqual(model_dict, expected)


class TestSODARCacheGetDateAPIView(SODARCacheViewTestBase):
    """Tests for SODARCacheGetDateAPIView"""

    def test_get(self):
        """Test SODARCacheGetDateAPIView GET"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        values = {'app_name': TEST_APP_NAME, 'name': ITEM_NAME}
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'sodarcache:cache_get_date',
                    kwargs={'project': self.project.sodar_uuid},
                ),
                values,
            )
        expected = self.cache_backend.get_update_time(
            app_name=TEST_APP_NAME, name=ITEM_NAME
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['update_time'], expected)
