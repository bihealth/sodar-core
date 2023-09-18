"""Test for REST API view permissions in the filesfolders app"""

import os
import uuid

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions_api import (
    TestCoreProjectAPIPermissionBase,
)

from filesfolders.models import File, HyperLink

from filesfolders.tests.test_permissions import FilesfoldersPermissionTestMixin


# Local constants
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'
TEST_DATA_PATH = os.path.dirname(__file__) + '/data/'
ZIP_PATH_NO_FILES = TEST_DATA_PATH + 'no_files.zip'
OBJ_UUID = uuid.uuid4()


class TestFolderListCreateAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests FolderListCreateAPIView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:api_folder_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.post_data = {
            'name': 'New Folder',
            'flag': 'IMPORTANT',
            'description': 'Description',
        }

    def test_get(self):
        """Test FolderListCreateAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_post(self):
        """Test FolderListCreateAPIView POST"""
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
            self.url, good_users, 201, method='POST', data=self.post_data
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
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
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
            self.url, good_users, 201, method='POST', data=self.post_data
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


class TestFolderRetrieveUpdateDestroyAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests FolderRetrieveUpdateDestroyAPIView permissions"""

    def _make_folder(self):
        folder = self.make_test_folder()
        folder.sodar_uuid = OBJ_UUID
        folder.save()
        return folder

    def setUp(self):
        super().setUp()
        folder = self._make_folder()
        self.url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': folder.sodar_uuid},
        )
        self.put_data = {
            'name': 'UPDATED Folder',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
        }
        self.patch_data = {'name': 'UPDATED Folder'}

    def test_get(self):
        """Test FolderRetrieveUpdateDestroyAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200, method='GET')
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
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
        self.assert_response_api(self.url, good_users, 200, method='GET')
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_put(self):
        """Test FolderRetrieveUpdateDestroyAPIView PUT"""
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
            self.url, good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test permissions for folder updating with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    def test_put_archive(self):
        """Test permissions for folder updating with PUT and archived project"""
        self.project.set_archive()
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
            self.url, good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
        )

    def test_patch(self):
        """Test FolderRetrieveUpdateDestroyAPIView PATCH"""
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
            self.url, good_users, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PATCH',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_patch_anon(self):
        """Test PATCH for with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_patch_archive(self):
        """Test PATCH with archived project"""
        self.project.set_archive()
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
            self.url, good_users, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )

    def test_delete(self):
        """Test FolderRetrieveUpdateDestroyAPIView DELETE"""
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
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
        )
        self.assert_response_api(self.url, bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_archive(self):
        """Test DELETEwith archived project"""
        self.project.set_archive()
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
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
        )
        self.assert_response_api(self.url, bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )


class TestFileListCreateAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests FileListCreateAPIView permissions"""

    def _make_post_data(self):
        self.post_data = {
            'name': 'New File',
            'flag': 'IMPORTANT',
            'description': 'File\'s description',
            'secret': 'foo',
            'public_url': True,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }

    def _cleanup(self):
        File.objects.all().delete()
        if hasattr(self, 'post_data'):
            self.post_data['file'].seek(0)

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:api_file_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def tearDown(self):
        if hasattr(self, 'post_data'):
            self.post_data['file'].close()
        super().tearDown()

    def test_get(self):
        """Test FileListCreateAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test permissions for file listing with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test permissions for file listing with archived project"""
        self.project.set_archive()
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_post(self):
        """Test FileListCreateAPIView POST"""
        self._make_post_data()
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
            self.url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        # self.request_data['file'].close()

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self._make_post_data()
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )

    def test_post_archive(self):
        """Test POST with archived project"""
        self._make_post_data()
        self.project.set_archive()
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
            self.url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            good_users,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )


class TestFileRetrieveUpdateDestroyAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests FileRetrieveUpdateDestroyAPIView permissions"""

    def _make_file(self):
        file = self.make_test_file()
        file.sodar_uuid = OBJ_UUID
        file.save()
        return file

    def _make_put_data(self):
        self.put_data = {
            'name': 'UPDATED File',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
            'secret': 'foo',
            'public_url': True,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }

    def _cleanup_put(self):
        self.put_data['file'].seek(0)

    def setUp(self):
        super().setUp()
        file = self._make_file()
        self.patch_data = {'name': 'UPDATED File'}
        self.url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': file.sodar_uuid},
        )

    def test_get(self):
        """Test FileRetrieveUpdateDestroyAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_put(self):
        """Test FileRetrieveUpdateDestroyAPIView PUT"""
        self._make_put_data()
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
            self.url,
            good_users,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        self._make_put_data()
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )

    def test_put_archive(self):
        """Test PUT with archived project"""
        self._make_put_data()
        self.project.set_archive()
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
            self.url,
            good_users,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )

    def test_patch(self):
        """Test FileRetrieveUpdateDestroyAPIView PATCH"""
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
            self.url,
            good_users,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_patch_anon(self):
        """Test PATCH with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )

    def test_patch_archive(self):
        """Test PATCH with archived project"""
        self.project.set_archive()
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
            self.url,
            good_users,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            bad_users,
            403,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )

    def test_delete(self):
        """Test FileRetrieveUpdateDestroyAPIView DELETE"""
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
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
        )
        self.assert_response_api(self.url, bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='DELETE',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_archive(self):
        """Test DELETE with archived project"""
        self.project.set_archive()
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
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
        )
        self.assert_response_api(self.url, bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )


class TestFileServeAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests FileServeAPIView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file()
        self.url = reverse(
            'filesfolders:api_file_serve', kwargs={'file': file.sodar_uuid}
        )

    def test_get(self):
        """Test FileServeAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200, method='GET')
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
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
        self.assert_response_api(self.url, good_users, 200, method='GET')
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)


class TestHyperLinkListCreateAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests HyperLinkListCreateAPIView permissions"""

    @classmethod
    def _cleanup(cls):
        HyperLink.objects.all().delete()

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:api_hyperlink_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.post_data = {
            'name': 'New HyperLink',
            'flag': 'IMPORTANT',
            'description': 'Description',
            'url': 'https://www.cubi.bihealth.org',
        }

    def test_get(self):
        """Test HyperLinkListCreateAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
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
        self.assert_response_api(self.url, good_users, 200)
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_post(self):
        """Test HyperLinkListCreateAPIView POST"""
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
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='POST',
            data=self.post_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
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
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='POST',
            data=self.post_data,
        )


class TestHyperLinkRetrieveUpdateDestroyAPIView(
    FilesfoldersPermissionTestMixin, TestCoreProjectAPIPermissionBase
):
    """Tests HyperLinkRetrieveUpdateDestroyAPIView permissions"""

    def _make_link(self):
        link = self.make_test_link()
        link.sodar_uuid = OBJ_UUID
        link.save()
        return link

    def _cleanup_delete(self):
        self._make_link()

    def setUp(self):
        super().setUp()
        link = self._make_link()
        self.url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': link.sodar_uuid},
        )
        self.put_data = {
            'name': 'UPDATED HyperLink',
            'flag': 'FLAG',
            'description': 'UPDATED description',
            'url': 'https://www.bihealth.org',
        }
        self.patch_data = {'name': 'UPDATED Hyperlink'}

    def test_get(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView GET"""
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
        self.assert_response_api(self.url, good_users, 200, method='GET')
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
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
        self.assert_response_api(self.url, good_users, 200, method='GET')
        self.assert_response_api(self.url, bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, good_users, 200, knox=True)
        self.project.set_public()
        self.assert_response_api(self.url, self.user_no_roles, 200)

    def test_put(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView PUT"""
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
            self.url, good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    def test_put_archive(self):
        """Test PUT with archived project"""
        self.project.set_archive()
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
            self.url, good_users, 200, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
        )

    def test_patch(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView PATCH"""
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
            self.url, good_users, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PATCH',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_patch_anon(self):
        """Test PATCH with anonymous access"""
        self.project.set_public()
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_patch_archive(self):
        """Test PATCH with archived project"""
        self.project.set_archive()
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
            self.url, good_users, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, bad_users, 403, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            good_users,
            200,
            method='PATCH',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )

    def test_delete(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView DELETE"""
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
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
        )
        self.assert_response_api(self.url, bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
            knox=True,
        )
        # Test public project
        self.project.set_public()
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='DELETE',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        self.project.set_public()
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_archive(self):
        """Test DELETE with archived project"""
        self.project.set_archive()
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
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
        )
        self.assert_response_api(self.url, bad_users, 403, method='DELETE')
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            good_users,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
            knox=True,
        )
        self.project.set_public()
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )
