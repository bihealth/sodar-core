"""REST API view permission tests for the filesfolders app"""

import os
import uuid

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions_api import (
    TestCoreProjectAPIPermissionBase,
)
from projectroles.utils import build_secret

from filesfolders.models import File, Folder, HyperLink
from filesfolders.tests.test_models import (
    FileMixin,
    FolderMixin,
    HyperLinkMixin,
)


# Local constants
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'
TEST_DATA_PATH = os.path.dirname(__file__) + '/data/'
ZIP_PATH_NO_FILES = TEST_DATA_PATH + 'no_files.zip'


class TestFolderAPIPermissions(FolderMixin, TestCoreProjectAPIPermissionBase):
    """Tests for Folder API view permissions"""

    @classmethod
    def _cleanup_folder_create(cls):
        Folder.objects.order_by('-pk').first().delete()

    def _cleanup_folder_destroy(self, obj_uuid):
        folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        folder.sodar_uuid = obj_uuid
        folder.save()

    def setUp(self):
        super().setUp()
        self.folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,  # Project owner is the owner of folder
            description='',
        )

    def test_folder_list(self):
        """Test permissions for folder listing"""
        url = reverse(
            'filesfolders:api_folder_list_create',
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_list_anon(self):
        """Test permissions for folder listing with anonymous access"""
        url = reverse(
            'filesfolders:api_folder_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_folder_list_archive(self):
        """Test permissions for folder listing with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_folder_list_create',
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    def test_folder_create(self):
        """Test permissions for folder creation"""
        url = reverse(
            'filesfolders:api_folder_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        request_data = {
            'name': 'New Folder',
            'flag': 'IMPORTANT',
            'description': 'Folder\'s description',
        }
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
            self.user_finder_cat,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_folder_create,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=request_data
        )
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_folder_create,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=request_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_create_anon(self):
        """Test permissions for folder creation with anonymous access"""
        url = reverse(
            'filesfolders:api_folder_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        request_data = {
            'name': 'New Folder',
            'flag': 'IMPORTANT',
            'description': 'Folder\'s description',
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=request_data
        )

    def test_folder_create_archive(self):
        """Test permissions for folder creation with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_folder_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        request_data = {
            'name': 'New Folder',
            'flag': 'IMPORTANT',
            'description': 'Folder\'s description',
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
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_folder_create,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=request_data
        )
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_folder_create,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=request_data
        )

    def test_folder_retrieve(self):
        """Test permissions for folder retrieval"""
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
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
        self.assert_response_api(url, good_users, 200, method='GET')
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_retrieve_anon(self):
        """Test permissions for folder retrieval with anonymous access"""
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_folder_retrieve_archive(self):
        """Test permissions for folder retrieval with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
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
        self.assert_response_api(url, good_users, 200, method='GET')
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    def test_folder_update_put(self):
        """Test permissions for folder updating with PUT"""
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        request_data = {
            'name': 'UPDATED Folder',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
        }
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of folder
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
            url, good_users, 200, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=request_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=request_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_update_put_anon(self):
        """Test permissions for folder updating with anonymous access"""
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        request_data = {
            'name': 'UPDATED Folder',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=request_data
        )

    def test_folder_update_put_archive(self):
        """Test permissions for folder updating with PUT and archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        request_data = {
            'name': 'UPDATED Folder',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
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
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=request_data
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=request_data
        )

    def test_folder_update_patch(self):
        """Test permissions for folder updating with PATCH"""
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        request_data = {'name': 'UPDATED Folder'}
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of folder
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
            url, good_users, 200, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, good_users, 200, method='PATCH', data=request_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PATCH', data=request_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_update_patch_anon(self):
        """Test permissions for folder updating with anonymous access"""
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        request_data = {'name': 'UPDATED Folder'}
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PATCH', data=request_data
        )

    def test_folder_update_patch_archive(self):
        """Test permissions for folder updating with PATCH and archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        request_data = {'name': 'UPDATED Folder'}
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
        self.assert_response_api(
            url, good_users, 200, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PATCH', data=request_data
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PATCH', data=request_data
        )

    def test_folder_destroy(self):
        """Test permissions for folder destroying with DELETE"""
        obj_uuid = uuid.uuid4()
        c_kwargs = {'obj_uuid': obj_uuid}
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': obj_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of folder
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
        self._cleanup_folder_destroy(**c_kwargs)
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_folder_destroy,
            cleanup_kwargs=c_kwargs,
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_folder_destroy,
            cleanup_kwargs=c_kwargs,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='DELETE')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_folder_destroy_anon(self):
        """Test permissions for folder destroying with anonymous access"""
        folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': folder.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')

    def test_folder_destroy_archive(self):
        """Test permissions for folder destroying with DELETE and archived project"""
        self.project.set_archive()
        obj_uuid = uuid.uuid4()
        c_kwargs = {'obj_uuid': obj_uuid}
        url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': obj_uuid},
        )
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
        self._cleanup_folder_destroy(**c_kwargs)
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_folder_destroy,
            cleanup_kwargs=c_kwargs,
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 403, method='DELETE')


class TestFileAPIPermissions(FileMixin, TestCoreProjectAPIPermissionBase):
    """Tests for File API view permissions"""

    def _cleanup_file_create(self):
        file = File.objects.filter(name=self.new_file_name).first()
        if file:
            file.delete()
        self.request_data['file'].seek(0)

    def _cleanup_file_update(self):
        self.request_data['file'].seek(0)

    def _cleanup_file_destroy(self, obj_uuid):
        file = self.make_file(
            name='file2.txt',
            file_name='file2.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=True,
            secret=build_secret(),
        )
        file.sodar_uuid = obj_uuid
        file.save()

    def setUp(self):
        super().setUp()
        self.file_content = bytes('content'.encode('utf-8'))
        self.file = self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=True,
            secret=SECRET,
        )
        self.new_file_name = 'New File'
        self.request_data = {
            'name': self.new_file_name,
            'flag': 'IMPORTANT',
            'description': 'File\'s description',
            'secret': 'foo',
            'public_url': True,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }

    def tearDown(self):
        self.request_data['file'].close()
        super().tearDown()

    def test_file_list(self):
        """Test permissions for file listing"""
        url = reverse(
            'filesfolders:api_file_list_create',
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_list_anon(self):
        """Test permissions for file listing with anonymous access"""
        url = reverse(
            'filesfolders:api_file_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_file_list_archive(self):
        """Test permissions for file listing with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_file_list_create',
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    def test_file_create(self):
        """Test permissions for file creation"""
        url = reverse(
            'filesfolders:api_file_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        # NOTE: Must call cleanup for ALL requests to seek the file
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
            self.user_finder_cat,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
        )
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='POST',
            format='multipart',
            data=self.request_data,
        )
        self.request_data['file'].close()

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_create_anon(self):
        """Test permissions for file creation with anonymous access"""
        url = reverse(
            'filesfolders:api_file_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
            format='multipart',
            data=self.request_data,
        )
        self.request_data['file'].close()

    def test_file_create_archive(self):
        """Test permissions for file creation with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_file_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
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
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
        )
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_create,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='POST',
            format='multipart',
            data=self.request_data,
        )
        self.request_data['file'].close()

    def test_file_retrieve(self):
        """Test permissions for file retrieval"""
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_retrieve_anon(self):
        """Test permissions for file retrieval with anonymous access"""
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_file_retrieve_archive(self):
        """Test permissions for file retrieval with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    def test_file_update_put(self):
        """Test permissions for file updating with PUT"""
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.request_data.update(
            {
                'name': 'UPDATED Folder',
                'flag': 'FLAG',
                'description': 'UPDATED Description',
            }
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of file
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
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            good_users,
            200,
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='PUT',
            format='multipart',
            data=self.request_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_update_put_anon(self):
        """Test permissions for file updating with anonymous access"""
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.request_data.update(
            {
                'name': 'UPDATED Folder',
                'flag': 'FLAG',
                'description': 'UPDATED Description',
            }
        )
        self.project.set_public()
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.request_data,
        )

    def test_file_update_put_archive(self):
        """Test permissions for file updating with PUT and archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.request_data.update(
            {
                'name': 'UPDATED Folder',
                'flag': 'FLAG',
                'description': 'UPDATED Description',
            }
        )
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
        self.assert_response_api(
            url,
            good_users,
            200,
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='PUT',
            format='multipart',
            data=self.request_data,
        )

    def test_file_update_patch(self):
        """Test permissions for file updating with PATCH"""
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.request_data.update({'name': 'UPDATED Folder'})
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of file
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
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            good_users,
            200,
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='PATCH',
            format='multipart',
            data=self.request_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_update_patch_anon(self):
        """Test permissions for file updating with anonymous access"""
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.request_data.update({'name': 'UPDATED Folder'})
        self.project.set_public()
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='PATCH',
            format='multipart',
            data=self.request_data,
        )

    def test_file_update_patch_archive(self):
        """Test permissions for file updating with PATCH and archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )
        self.request_data.update({'name': 'UPDATED Folder'})
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
        self.assert_response_api(
            url,
            good_users,
            200,
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            bad_users,
            403,
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='PATCH',
            format='multipart',
            data=self.request_data,
            cleanup_method=self._cleanup_file_update,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='PATCH',
            format='multipart',
            data=self.request_data,
        )

    def test_file_destroy(self):
        """Test permissions for file destroying with DELETE"""
        obj_uuid = uuid.uuid4()
        c_kwargs = {'obj_uuid': obj_uuid}
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': obj_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of file
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
        self._cleanup_file_destroy(**c_kwargs)
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_file_destroy,
            cleanup_kwargs=c_kwargs,
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_file_destroy,
            cleanup_kwargs=c_kwargs,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='DELETE',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_destroy_anon(self):
        """Test permissions for file destroying with anonymous access"""
        file = self.make_file(
            name='file2.txt',
            file_name='file2.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=True,
            secret=build_secret(),
        )
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': file.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='DELETE',
        )

    def test_file_destroy_archive(self):
        """Test permissions for file destroying with DELETE and archived project"""
        self.project.set_archive()
        obj_uuid = uuid.uuid4()
        c_kwargs = {'obj_uuid': obj_uuid}
        url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': obj_uuid},
        )
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
        self._cleanup_file_destroy(**c_kwargs)
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_file_destroy,
            cleanup_kwargs=c_kwargs,
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='DELETE',
        )

    def test_file_serve(self):
        """Test permissions for file serving"""
        url = reverse(
            'filesfolders:api_file_serve', kwargs={'file': self.file.sodar_uuid}
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
        self.assert_response_api(url, good_users, 200, method='GET')
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_file_serve_anon(self):
        """Test permissions for file serving with anonymous access"""
        url = reverse(
            'filesfolders:api_file_serve', kwargs={'file': self.file.sodar_uuid}
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_file_serve_archive(self):
        """Test permissions for file serving with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_file_serve', kwargs={'file': self.file.sodar_uuid}
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
        self.assert_response_api(url, good_users, 200, method='GET')
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)


class TestHyperLinkAPIPermissions(
    HyperLinkMixin, TestCoreProjectAPIPermissionBase
):
    """Tests for HyperLink API view permissions"""

    @classmethod
    def _cleanup_link_create(cls):
        HyperLink.objects.order_by('-pk').first().delete()

    def _cleanup_link_destroy(self, obj_uuid):
        link = self.make_hyperlink(
            name='New Link',
            url='http://www.duckduckgo.com/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        link.sodar_uuid = obj_uuid
        link.save()

    def setUp(self):
        super().setUp()
        self.hyperlink = self.make_hyperlink(
            name='Link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )

    def test_hyperlink_list(self):
        """Test permissions for hyperlink listing"""
        url = reverse(
            'filesfolders:api_hyperlink_list_create',
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_list_anon(self):
        """Test permissions for hyperlink listing with anonymous access"""
        url = reverse(
            'filesfolders:api_hyperlink_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_hyperlink_list_archive(self):
        """Test permissions for hyperlink listing with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_hyperlink_list_create',
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    def test_hyperlink_create(self):
        """Test permissions for hyperlink creation"""
        url = reverse(
            'filesfolders:api_hyperlink_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        request_data = {
            'name': 'New HyperLink',
            'flag': 'IMPORTANT',
            'description': 'HyperLink\'s description',
            'url': 'http://www.cubi.bihealth.org',
        }

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
            self.user_finder_cat,
            self.user_guest,
            self.user_no_roles,
        ]
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_link_create,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=request_data
        )
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_link_create,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=request_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_create_anon(self):
        """Test permissions for hyperlink creation with anonymous access"""
        url = reverse(
            'filesfolders:api_hyperlink_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        request_data = {
            'name': 'New HyperLink',
            'flag': 'IMPORTANT',
            'description': 'HyperLink\'s description',
            'url': 'http://www.cubi.bihealth.org',
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=request_data
        )

    def test_hyperlink_create_archive(self):
        """Test permissions for hyperlink creation with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_hyperlink_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        request_data = {
            'name': 'New HyperLink',
            'flag': 'IMPORTANT',
            'description': 'HyperLink\'s description',
            'url': 'http://www.cubi.bihealth.org',
        }

        good_users = [self.superuser]
        bad_users = [
            self.user_owner,
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
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_link_create,
        )
        self.assert_response_api(
            url, bad_users, 403, method='POST', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='POST', data=request_data
        )
        self.assert_response_api(
            url,
            good_users,
            201,
            method='POST',
            data=request_data,
            cleanup_method=self._cleanup_link_create,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='POST', data=request_data
        )

    def test_hyperlink_retrieve(self):
        """Test permissions for hyperlink retrieval"""
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
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
        self.assert_response_api(url, good_users, 200, method='GET')
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_retrieve_anon(self):
        """Test permissions for hyperlink retrieval with anonymous access"""
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(url, self.anonymous, 200)

    def test_hyperlink_retrieve_archive(self):
        """Test permissions for hyperlink retrieval with archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
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
        self.assert_response_api(url, good_users, 200, method='GET')
        self.assert_response_api(url, bad_users, 403)
        self.assert_response_api(url, self.anonymous, 401)
        self.assert_response_api(url, good_users, 200, knox=True)
        # Test public project
        self.project.set_public()
        self.assert_response_api(url, self.user_no_roles, 200)

    def test_hyperlink_update_put(self):
        """Test permissions for hyperlink updating with PUT"""
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        request_data = {
            'name': 'UPDATED HyperLink',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
            'url': 'http://www.bihealth.org',
        }
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of link
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
            url, good_users, 200, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=request_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=request_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_update_put_anon(self):
        """Test permissions for hyperlink updating with anonymous access"""
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        request_data = {
            'name': 'UPDATED HyperLink',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
            'url': 'http://www.bihealth.org',
        }
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=request_data
        )

    def test_hyperlink_update_put_archive(self):
        """Test permissions for hyperlink updating with PUT and archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        request_data = {
            'name': 'UPDATED HyperLink',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
            'url': 'http://www.bihealth.org',
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
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PUT', data=request_data
        )
        self.assert_response_api(
            url, good_users, 200, method='PUT', data=request_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PUT', data=request_data
        )

    def test_hyperlink_update_patch(self):
        """Test permissions for hyperlink updating with PATCH"""
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        request_data = {'name': 'UPDATED Hyperlink'}
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of link
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
            url, good_users, 200, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, good_users, 200, method='PATCH', data=request_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PATCH', data=request_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_update_patch_anon(self):
        """Test permissions for hyperlink updating with anonymous access"""
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        request_data = {'name': 'UPDATED Hyperlink'}
        self.project.set_public()
        self.assert_response_api(
            url, self.anonymous, 401, method='PATCH', data=request_data
        )

    def test_hyperlink_update_patch_archive(self):
        """Test permissions for hyperlink updating with PATCH and archived project"""
        self.project.set_archive()
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )
        request_data = {'name': 'UPDATED Hyperlink'}
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
        self.assert_response_api(
            url, good_users, 200, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, bad_users, 403, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, self.anonymous, 401, method='PATCH', data=request_data
        )
        self.assert_response_api(
            url, good_users, 200, method='PATCH', data=request_data, knox=True
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url, self.user_no_roles, 403, method='PATCH', data=request_data
        )

    def test_hyperlink_destroy(self):
        """Test permissions for hyperlink destroying with DELETE"""
        obj_uuid = uuid.uuid4()
        c_kwargs = {'obj_uuid': obj_uuid}
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': obj_uuid},
        )
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of link
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
        self._cleanup_link_destroy(**c_kwargs)
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_link_destroy,
            cleanup_kwargs=c_kwargs,
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_link_destroy,
            cleanup_kwargs=c_kwargs,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='DELETE',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_hyperlink_destroy_anon(self):
        """Test permissions for hyperlink destroying with anonymous access"""
        link = self.make_hyperlink(
            name='New Link',
            url='http://www.duckduckgo.com/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': link.sodar_uuid},
        )
        self.project.set_public()
        self.assert_response_api(
            url,
            self.anonymous,
            401,
            method='DELETE',
        )

    def test_hyperlink_destroy_archive(self):
        """Test permissions for hyperlink destroying with DELETE and archived project"""
        self.project.set_archive()
        obj_uuid = uuid.uuid4()
        c_kwargs = {'obj_uuid': obj_uuid}
        url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': obj_uuid},
        )
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
        self._cleanup_link_destroy(**c_kwargs)
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_link_destroy,
            cleanup_kwargs=c_kwargs,
        )
        self.assert_response_api(url, bad_users, 403, method='DELETE')
        self.assert_response_api(url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_link_destroy,
            cleanup_kwargs=c_kwargs,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            url,
            self.user_no_roles,
            403,
            method='DELETE',
        )
