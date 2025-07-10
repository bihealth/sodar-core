"""Test for REST API view permissions in the filesfolders app"""

import os
import uuid

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.tests.test_permissions_api import ProjectAPIPermissionTestBase

from filesfolders.models import File, Folder, HyperLink
from filesfolders.tests.test_permissions import FilesfoldersPermissionTestMixin
from filesfolders.views_api import (
    FILESFOLDERS_API_MEDIA_TYPE,
    FILESFOLDERS_API_DEFAULT_VERSION,
)


# Local constants
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'
TEST_DATA_PATH = os.path.dirname(__file__) + '/data/'
ZIP_PATH_NO_FILES = TEST_DATA_PATH + 'no_files.zip'
OBJ_UUID = uuid.uuid4()


class FilesfoldersAPIPermissionTestBase(
    FilesfoldersPermissionTestMixin, ProjectAPIPermissionTestBase
):
    """Base class for filesfolders REST API view permission tests"""

    media_type = FILESFOLDERS_API_MEDIA_TYPE
    api_version = FILESFOLDERS_API_DEFAULT_VERSION


class TestFolderListCreateAPIView(FilesfoldersAPIPermissionTestBase):
    """Tests for FolderListCreateAPIView permissions"""

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
        self.good_users_get = [
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
        self.bad_users_get = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]

    def test_get(self):
        """Test FolderListCreateAPIView GET"""
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

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
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_viewer,
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
        self.project.set_public_access(self.role_guest)
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
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url, self.superuser, 201, method='POST', data=self.post_data
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
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
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
            self.url, self.superuser, 201, method='POST', data=self.post_data
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
            self.url, self.superuser, 201, method='POST', data=self.post_data
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


class TestFolderRetrieveUpdateDestroyAPIView(FilesfoldersAPIPermissionTestBase):
    """Tests for FolderRetrieveUpdateDestroyAPIView permissions"""

    def _make_folder(self) -> Folder:
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
        self.good_users_get = [
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
        self.bad_users_get = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]
        self.good_users_update = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users_update = [
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
        """Test FolderRetrieveUpdateDestroyAPIView GET"""
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_put(self):
        """Test FolderRetrieveUpdateDestroyAPIView PUT"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url,
            self.bad_users_update,
            403,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    def test_put_archive(self):
        """Test PUT with archived project"""
        self.project.set_archive()
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
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
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

    def test_patch(self):
        """Test FolderRetrieveUpdateDestroyAPIView PATCH"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.bad_users_update,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PATCH',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            data=self.patch_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_patch_anon(self):
        """Test PATCH for with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_patch_archive(self):
        """Test PATCH with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url, self.superuser, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            data=self.patch_data,
        )

    def test_patch_block(self):
        """Test PATCH with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url, self.superuser, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_patch_read_only(self):
        """Test PATCH with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.superuser, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_delete(self):
        """Test FolderRetrieveUpdateDestroyAPIView DELETE"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
        )
        self.assert_response_api(
            self.url, self.bad_users_update, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.good_users_update,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            data=self.patch_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_archive(self):
        """Test DELETE with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            data=self.patch_data,
        )

    def test_delete_block(self):
        """Test DELETE with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._make_folder,
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
            cleanup_method=self._make_folder,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')


class TestFileListCreateAPIView(FilesfoldersAPIPermissionTestBase):
    """Tests for FileListCreateAPIView permissions"""

    def _make_post_data(self) -> dict:
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
        self.good_users_get = [
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
        self.bad_users_get = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]

    def tearDown(self):
        if hasattr(self, 'post_data'):
            self.post_data['file'].close()
        super().tearDown()

    def test_get(self):
        """Test FileListCreateAPIView GET"""
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

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
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_viewer,
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
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
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

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self._make_post_data()
        self.project.set_public_access(self.role_guest)
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
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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
            self.superuser,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
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

    def test_post_block(self):
        """Test POST with project access block"""
        self.set_access_block(self.project)
        self._make_post_data()
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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

    def test_post_read_only(self):
        """Test POST with site read-only mode"""
        self.set_site_read_only()
        self._make_post_data()
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            format='multipart',
            data=self.post_data,
            cleanup_method=self._cleanup,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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


class TestFileRetrieveUpdateDestroyAPIView(FilesfoldersAPIPermissionTestBase):
    """Tests for FileRetrieveUpdateDestroyAPIView permissions"""

    def _make_file(self) -> File:
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
        self.good_users_get = [
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
        self.bad_users_get = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]
        self.good_users_update = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,
            self.user_delegate,
        ]
        self.bad_users_update = [
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
        """Test FileRetrieveUpdateDestroyAPIView GET"""
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_put(self):
        """Test FileRetrieveUpdateDestroyAPIView PUT"""
        self._make_put_data()
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            self.bad_users_update,
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
            self.good_users_update,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self._make_put_data()
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
        self.project.set_archive()
        self._make_put_data()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PUT',
            format='multipart',
            data=self.put_data,
        )

    def test_put_block(self):
        """Test PUT with project access block"""
        self.set_access_block(self.project)
        self._make_put_data()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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

    def test_put_read_only(self):
        """Test PUT with site read-only mode"""
        self.set_site_read_only()
        self._make_put_data()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PUT',
            format='multipart',
            data=self.put_data,
            cleanup_method=self._cleanup_put,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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

    def test_patch(self):
        """Test FileRetrieveUpdateDestroyAPIView PATCH"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.bad_users_update,
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
            self.good_users_update,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
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

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_patch_anon(self):
        """Test PATCH with anonymous access"""
        self.project.set_public_access(self.role_guest)
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
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
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

    def test_patch_block(self):
        """Test PATCH with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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

    def test_patch_read_only(self):
        """Test PATCH with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PATCH',
            format='multipart',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
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

    def test_delete(self):
        """Test FileRetrieveUpdateDestroyAPIView DELETE"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
        )
        self.assert_response_api(
            self.url, self.bad_users_update, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.good_users_update,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='DELETE',
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='DELETE',
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_archive(self):
        """Test DELETE with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_block(self):
        """Test DELETE with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._make_file,
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
            cleanup_method=self._make_file,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')


class TestFileServeAPIView(FilesfoldersAPIPermissionTestBase):
    """Tests for FileServeAPIView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file()
        self.url = reverse(
            'filesfolders:api_file_serve', kwargs={'file': file.sodar_uuid}
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
        self.bad_users = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]

    def test_get(self):
        """Test FileServeAPIView GET"""
        self.assert_response_api(self.url, self.good_users, 200, method='GET')
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users, 200, method='GET')
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users, 200, method='GET')
        self.assert_response_api(self.url, self.bad_users, 403)
        self.assert_response_api(self.url, self.anonymous, 401)


class TestHyperLinkListCreateAPIView(FilesfoldersAPIPermissionTestBase):
    """Tests for HyperLinkListCreateAPIView permissions"""

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
        self.good_users_get = [
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
        self.bad_users_get = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]

    def test_get(self):
        """Test HyperLinkListCreateAPIView GET"""
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

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
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_guest,
            self.user_viewer,
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
        self.project.set_public_access(self.role_guest)
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
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.anonymous, 401, method='POST', data=self.post_data
        )

    def test_post_archive(self):
        """Test POST with archived project"""
        self.project.set_archive()
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
        self.assert_response_api(
            self.url,
            self.superuser,
            201,
            method='POST',
            data=self.post_data,
            cleanup_method=self._cleanup,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
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


class TestHyperLinkRetrieveUpdateDestroyAPIView(
    FilesfoldersAPIPermissionTestBase
):
    """Tests for HyperLinkRetrieveUpdateDestroyAPIView permissions"""

    def _make_link(self) -> HyperLink:
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
        self.good_users_get = [
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
        self.bad_users_get = [
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_viewer,
            self.user_no_roles,
        ]
        self.good_users_update = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_owner,  # Owner of link
            self.user_delegate,
        ]
        self.bad_users_update = [
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
        """Test HyperLinkRetrieveUpdateDestroyAPIView GET"""
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 200)

    def test_get_archive(self):
        """Test GET with archived project"""
        self.project.set_archive()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)
        self.assert_response_api(self.url, self.good_users_get, 200, knox=True)
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.user_no_roles, 200)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_block(self):
        """Test GET with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(self.url, self.superuser, 200)
        self.assert_response_api(self.url, self.auth_non_superusers, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_get_read_only(self):
        """Test GET with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(self.url, self.good_users_get, 200)
        self.assert_response_api(self.url, self.bad_users_get, 403)
        self.assert_response_api(self.url, self.anonymous, 401)

    def test_put(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView PUT"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url,
            self.bad_users_update,
            403,
            method='PUT',
            data=self.put_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_put_anon(self):
        """Test PUT with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PUT', data=self.put_data
        )

    def test_put_archive(self):
        """Test PUT with archived project"""
        self.project.set_archive()
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
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PUT',
            data=self.put_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='PUT', data=self.put_data
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

    def test_patch(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView PATCH"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.bad_users_update,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.good_users_update,
            200,
            method='PATCH',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            data=self.patch_data,
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_patch_anon(self):
        """Test PATCH with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_patch_archive(self):
        """Test PATCH with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url, self.superuser, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.superuser,
            200,
            method='PATCH',
            data=self.patch_data,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url,
            self.anonymous,
            401,
            method='PATCH',
            data=self.patch_data,
        )

    def test_patch_block(self):
        """Test PATCH with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url, self.superuser, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_patch_read_only(self):
        """Test PATCH with site read-only mode"""
        self.set_site_read_only()
        self.assert_response_api(
            self.url, self.superuser, 200, method='PATCH', data=self.patch_data
        )
        self.assert_response_api(
            self.url,
            self.auth_non_superusers,
            403,
            method='PATCH',
            data=self.patch_data,
        )
        self.assert_response_api(
            self.url, self.anonymous, 401, method='PATCH', data=self.patch_data
        )

    def test_delete(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView DELETE"""
        self.assert_response_api(
            self.url,
            self.good_users_update,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
        )
        self.assert_response_api(
            self.url, self.bad_users_update, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.good_users_update,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
            knox=True,
        )
        # Test public project
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url,
            self.user_no_roles,
            403,
            method='DELETE',
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_delete_anon(self):
        """Test DELETE with anonymous access"""
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_archive(self):
        """Test DELETE with archived project"""
        self.project.set_archive()
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
            knox=True,
        )
        self.project.set_public_access(self.role_guest)
        self.assert_response_api(
            self.url, self.user_no_roles, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')

    def test_delete_block(self):
        """Test DELETE with project access block"""
        self.set_access_block(self.project)
        self.assert_response_api(
            self.url,
            self.superuser,
            204,
            method='DELETE',
            cleanup_method=self._cleanup_delete,
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
            cleanup_method=self._cleanup_delete,
        )
        self.assert_response_api(
            self.url, self.auth_non_superusers, 403, method='DELETE'
        )
        self.assert_response_api(self.url, self.anonymous, 401, method='DELETE')
