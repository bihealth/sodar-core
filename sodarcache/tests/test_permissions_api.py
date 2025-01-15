"""REST API view permission tests for the sodarcache app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.plugins import get_backend_api
from projectroles.tests.test_permissions_api import ProjectAPIPermissionTestBase

from sodarcache.tests.test_views_api import (
    TEST_APP_NAME,
    ITEM_NAME,
    DATA_KEY,
    DATA_VAL,
)
from sodarcache.views_api import (
    SODARCACHE_API_MEDIA_TYPE,
    SODARCACHE_API_DEFAULT_VERSION,
)


class SodarcacheAPIPermissionTestBase(ProjectAPIPermissionTestBase):
    """Base class for sodarcache REST API view permission tests"""

    media_type = SODARCACHE_API_MEDIA_TYPE
    api_version = SODARCACHE_API_DEFAULT_VERSION

    def setUp(self):
        super().setUp()
        self.cache_backend = get_backend_api('sodar_cache')


class TestCacheItemRetrieveAPIView(SodarcacheAPIPermissionTestBase):
    """Test CacheItemRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        # Init cache item
        self.item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name=ITEM_NAME,
            data={DATA_KEY: DATA_VAL},
        )
        self.url = reverse(
            'sodarcache:api_retrieve',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
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
        self.bad_users = [self.user_finder_cat, self.user_no_roles]

    def test_get(self):
        """Test CacheItemRetrieveAPIView GET"""
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestCacheItemDateRetrieveAPIView(SodarcacheAPIPermissionTestBase):
    """Test CacheItemDateRetrieveAPIView permissions"""

    def setUp(self):
        super().setUp()
        # Init cache item
        self.item = self.cache_backend.set_cache_item(
            project=self.project,
            app_name=TEST_APP_NAME,
            user=self.user_owner,
            name=ITEM_NAME,
            data={DATA_KEY: DATA_VAL},
        )
        self.url = reverse(
            'sodarcache:api_retrieve_date',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
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
        self.bad_users = [self.user_finder_cat, self.user_no_roles]

    def test_get(self):
        """Test CacheItemDateRetrieveAPIView GET"""
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users, 200)
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestCacheItemSetAPIView(SodarcacheAPIPermissionTestBase):
    """Test CacheItemSetAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'sodarcache:api_set',
            kwargs={
                'project': self.project.sodar_uuid,
                'app_name': TEST_APP_NAME,
                'item_name': ITEM_NAME,
            },
        )
        self.post_data = {'data': {DATA_KEY: DATA_VAL}}
        self.good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        self.bad_users = [
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_no_roles,
        ]

    def test_post(self):
        """Test CacheItemSetAPIView POST"""
        self.assert_response_api(
            self.url, self.good_users, 200, method='POST', data=self.post_data
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
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='POST',
            data=self.post_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url, self.good_users, 200, method='POST', data=self.post_data
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
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='POST',
            data=self.post_data,
        )

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.good_users, 200, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.bad_users, 403, method='POST', data=self.post_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )
