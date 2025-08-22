"""Tests for the API in the sodarcache app"""

from django.forms.models import model_to_dict

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAPI


from sodarcache.models import JSONCacheItem
from sodarcache.tests.test_models import (
    JSONCacheItemTestBase,
    JSONCacheItemMixin,
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
APP_NAME = 'sodarcache'
INVALID_APP_NAME = 'timeline'  # Valid app name but but no data is created


class TestSodarCacheAPI(JSONCacheItemMixin, JSONCacheItemTestBase):
    """Testing sodarcache API class"""

    def setUp(self):
        super().setUp()
        self.cache_backend = plugin_api.get_backend_api('sodar_cache')

    def test_get_model(self):
        """Test get_model()"""
        self.assertEqual(self.cache_backend.get_model(), JSONCacheItem)

    def test_set_cache_item(self):
        """Test set_cache_item() to create item"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)
        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': APP_NAME,
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': item.sodar_uuid,
        }
        self.assertEqual(model_to_dict(item), expected)

    def test_set_cache_item_invalid_app_name(self):
        """Test set_cache_item() with invalid app name"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)
        with self.assertRaises(ValueError):
            self.cache_backend.set_cache_item(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                name='test_item',
                data={'test_key': 'test_val'},
            )
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_set_cache_item_invalid_data_type(self):
        """Test set_cache_item() with invalid data type"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)
        with self.assertRaises(ValueError):
            self.cache_backend.set_cache_item(
                project=self.project,
                app_name='NON-EXISTING APP NAME',
                user=self.user_owner,
                name='test_item',
                data_type='INVALID DATA TYPE',
                data={'test_key': 'test_val'},
            )
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_set_cache_item_update(self):
        """Test set_cache_item() to update existing event"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)
        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        update_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'new_test_val'},
        )
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': APP_NAME,
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'new_test_val'},
            'sodar_uuid': item.sodar_uuid,
        }
        self.assertEqual(model_to_dict(update_item), expected)

    def test_set_cache_item_update_no_user(self):
        """Test set_cache_item() to update item with no user"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)
        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        update_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            name='test_item',
            data={'test_key': 'new_test_val'},
        )
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': APP_NAME,
            'user': None,
            'name': 'test_item',
            'data': {'test_key': 'new_test_val'},
            'sodar_uuid': item.sodar_uuid,
        }
        self.assertEqual(model_to_dict(update_item), expected)

    def test_get_cache_item(self):
        """Test get_cache_item()"""
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)
        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        get_item = self.cache_backend.get_cache_item(
            app_name=APP_NAME, name='test_item', project=self.project
        )
        expected = {
            'id': item.pk,
            'project': self.project.pk,
            'app_name': APP_NAME,
            'user': self.user_owner.pk,
            'name': 'test_item',
            'data': {'test_key': 'test_val'},
            'sodar_uuid': item.sodar_uuid,
        }
        self.assertEqual(model_to_dict(get_item), expected)

    def test_delete_cache_item(self):
        """Test delete_cache_item()"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        item = self.cache_backend.get_cache_item(
            app_name=APP_NAME, name='test_item', project=self.project
        )
        self.assertIsNotNone(item)
        self.cache_backend.delete_cache_item(
            app_name=APP_NAME, name='test_item', project=self.project
        )
        item = self.cache_backend.get_cache_item(
            app_name=APP_NAME, name='test_item', project=self.project
        )
        self.assertIsNone(item)
        # Test for deleting a non-existing item
        self.cache_backend.delete_cache_item(
            app_name=APP_NAME, name='test_item', project=self.project
        )

    def test_get_project_cache(self):
        """Test get_project_cache()"""
        first_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item1',
            data={'test_key1': 'test_val1'},
        )
        second_item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item2',
            data={'test_key2': 'test_val2'},
        )
        project_items = self.cache_backend.get_project_cache(
            project=self.project, data_type='json'
        )
        self.assertEqual(project_items.count(), 2)
        self.assertIn(first_item, project_items)
        self.assertIn(second_item, project_items)

    def test_get_update_time(self):
        """Test get_update_time()"""
        item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        update_time = self.cache_backend.get_update_time(
            app_name=APP_NAME, name='test_item', project=self.project
        )
        self.assertEqual(update_time, item.date_modified.timestamp())

    def test_delete_cache(self):
        """Test delete_cache()"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache()
        self.assertEqual(delete_status, 1)
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_delete_cache_app_name(self):
        """Test delete_cache() with app name"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(app_name=APP_NAME)
        self.assertEqual(delete_status, 1)
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_delete_cache_app_name_no_items(self):
        """Test delete_cache() with app name and no created items"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(
            app_name=INVALID_APP_NAME
        )
        self.assertEqual(delete_status, 0)
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)

    def test_delete_cache_project(self):
        """Test delete_cache() with project"""
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(project=self.project)
        self.assertEqual(delete_status, 1)
        self.assertEqual(JSONCacheItem.objects.all().count(), 0)

    def test_delete_cache_project_no_items(self):
        """Test delete_cache() with project and no created items"""
        new_project = self.make_project(
            'NewProject', PROJECT_TYPE_PROJECT, None
        )
        self.cache_backend.set_cache_item(
            project=self.project,
            app_name=APP_NAME,
            user=self.user_owner,
            name='test_item',
            data={'test_key': 'test_val'},
        )
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
        delete_status = self.cache_backend.delete_cache(project=new_project)
        self.assertEqual(delete_status, 0)
        self.assertEqual(JSONCacheItem.objects.all().count(), 1)
