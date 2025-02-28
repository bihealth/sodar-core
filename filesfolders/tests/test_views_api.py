"""REST API view tests for the filesfolders app"""

import json

from django.urls import reverse

from test_plus.test import APITestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_views_api import SODARAPIViewTestMixin
from projectroles.views_api import INVALID_PROJECT_TYPE_MSG

from filesfolders.tests.test_views import (
    ZIP_PATH_NO_FILES,
    FilesfoldersViewTestMixin,
)
from filesfolders.models import Folder, File, HyperLink
from filesfolders.views_api import (
    FILESFOLDERS_API_MEDIA_TYPE,
    FILESFOLDERS_API_DEFAULT_VERSION,
)


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']

# Local constants
INVALID_UUID = '11111111-1111-1111-1111-111111111111'


class FilesfoldersAPIViewTestBase(
    FilesfoldersViewTestMixin, SODARAPIViewTestMixin, APITestCase
):
    """Base class for filesfolders API tests"""

    media_type = FILESFOLDERS_API_MEDIA_TYPE
    api_version = FILESFOLDERS_API_DEFAULT_VERSION

    def setUp(self):
        super().setUp()
        # Get knox token for self.user
        self.knox_token = self.get_token(self.user)


class TestFolderListCreateAPIView(FilesfoldersAPIViewTestBase):
    """Tests for FolderListCreateAPIView"""

    def setUp(self):
        super().setUp()
        self.folder_data = {
            'name': 'New Folder',
            'flag': 'IMPORTANT',
            'description': 'Folder\'s description',
        }
        self.url = reverse(
            'filesfolders:api_folder_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get_list(self):
        """Test FolderListCreateAPIView GET to list folders"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.folder.name,
            'folder': None,
            'owner': str(self.folder.owner.sodar_uuid),
            'project': str(self.folder.project.sodar_uuid),
            'flag': self.folder.flag,
            'description': self.folder.description,
            'date_modified': self.get_drf_datetime(self.folder.date_modified),
            'sodar_uuid': str(self.folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), [expected])

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.folder.name,
                    'folder': None,
                    'owner': str(self.folder.owner.sodar_uuid),
                    'project': str(self.folder.project.sodar_uuid),
                    'flag': self.folder.flag,
                    'description': self.folder.description,
                    'date_modified': self.get_drf_datetime(
                        self.folder.date_modified
                    ),
                    'sodar_uuid': str(self.folder.sodar_uuid),
                }
            ],
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_create_root(self):
        """Test POST to create folder in root"""
        response = self.request_knox(
            self.url, method='POST', data=self.folder_data
        )
        self.assertEqual(response.status_code, 201, msg=response.data)
        new_folder = Folder.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_folder)
        expected = {
            **self.folder_data,
            'folder': None,
            'owner': str(self.user.sodar_uuid),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_folder.date_modified),
            'sodar_uuid': str(new_folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_create_folder(self):
        """Test POST to create folder under folder"""
        folder_data = {
            **self.folder_data,
            'folder': str(self.folder.sodar_uuid),
        }
        response = self.request_knox(self.url, method='POST', data=folder_data)
        self.assertEqual(response.status_code, 201, msg=response.data)
        new_folder = Folder.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_folder)
        expected = {
            **folder_data,
            'owner': str(self.user.sodar_uuid),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_folder.date_modified),
            'sodar_uuid': str(new_folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_create_category(self):
        """Test POST to create folder in category (should fail)"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_list_create',
                kwargs={'project': category.sodar_uuid},
            ),
            method='POST',
            data=self.folder_data,
        )
        self.assertEqual(response.status_code, 403, msg=response.data)
        self.assertEqual(
            str(response.data['detail']),
            INVALID_PROJECT_TYPE_MSG.format(project_type=PROJECT_TYPE_CATEGORY),
        )


class TestFolderRetrieveUpdateDestroyAPIView(FilesfoldersAPIViewTestBase):
    """Tests for FolderRetrieveUpdateDestroyAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:api_folder_retrieve_update_destroy',
            kwargs={'folder': self.folder.sodar_uuid},
        )

    def test_get_retrieve(self):
        """Test FolderRetrieveUpdateDestroyAPIView GET to retrieve folder"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.folder.name,
            'folder': None,
            'owner': str(self.folder.owner.sodar_uuid),
            'project': str(self.folder.project.sodar_uuid),
            'flag': self.folder.flag,
            'description': self.folder.description,
            'date_modified': self.get_drf_datetime(self.folder.date_modified),
            'sodar_uuid': str(self.folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_folder_retrieve_update_destroy',
                kwargs={'folder': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_put_update(self):
        """Test PUT to update folder"""
        folder_data = {
            'name': 'UPDATED Folder',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
        }
        response = self.request_knox(self.url, method='PUT', data=folder_data)
        self.assertEqual(response.status_code, 200, msg=response.data)
        self.folder.refresh_from_db()
        expected = {
            **folder_data,
            'folder': None,
            'owner': str(self.folder.owner.sodar_uuid),
            'project': str(self.folder.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(self.folder.date_modified),
            'sodar_uuid': str(self.folder.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_delete(self):
        """Test DELETE to remove folder"""
        response = self.request_knox(self.url, method='DELETE')
        self.assertEqual(response.status_code, 204, msg=response.data)
        self.assertIsNone(response.data)
        with self.assertRaises(Folder.DoesNotExist):
            Folder.objects.get(
                project=self.project, sodar_uuid=self.folder.sodar_uuid
            )


class TestFileListCreateAPIView(FilesfoldersAPIViewTestBase):
    """Tests for FileListCreateAPIView"""

    def setUp(self):
        super().setUp()
        self.file_data = {
            'name': 'New File',
            'flag': 'IMPORTANT',
            'description': 'File\'s description',
            'secret': 'foo',
            'public_url': True,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }
        self.url = reverse(
            'filesfolders:api_file_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def tearDown(self):
        self.file_data['file'].close()
        super().tearDown()

    def test_get_list(self):
        """Test FileListCreateAPIView GET to list files"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.file.name,
            'folder': None,
            'owner': str(self.file.owner.sodar_uuid),
            'project': str(self.file.project.sodar_uuid),
            'flag': self.file.flag,
            'description': self.file.description,
            'secret': self.file.secret,
            'public_url': self.file.public_url,
            'date_modified': self.get_drf_datetime(self.file.date_modified),
            'sodar_uuid': str(self.file.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), [expected])

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.file.name,
                    'folder': None,
                    'owner': str(self.file.owner.sodar_uuid),
                    'project': str(self.file.project.sodar_uuid),
                    'flag': self.file.flag,
                    'description': self.file.description,
                    'secret': self.file.secret,
                    'public_url': self.file.public_url,
                    'date_modified': self.get_drf_datetime(
                        self.file.date_modified
                    ),
                    'sodar_uuid': str(self.file.sodar_uuid),
                }
            ],
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_create_root(self):
        """Test POST to create file in root"""
        response = self.request_knox(
            self.url, method='POST', format='multipart', data=self.file_data
        )
        self.assertEqual(response.status_code, 201, msg=response.data)
        new_file = File.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_file)
        self.assertNotEqual(new_file.file.file.size, 0)
        expected = {
            **self.file_data,
            'folder': None,
            'owner': str(self.user.sodar_uuid),
            'project': str(self.project.sodar_uuid),
            'secret': new_file.secret,
            'public_url': new_file.public_url,
            'date_modified': self.get_drf_datetime(new_file.date_modified),
            'sodar_uuid': str(new_file.sodar_uuid),
        }
        expected.pop('file')
        self.assertEqual(json.loads(response.content), expected)

    def test_post_create_folder(self):
        """Test POST to create file under folder"""
        file_data = {**self.file_data, 'folder': str(self.folder.sodar_uuid)}
        response = self.request_knox(
            self.url, method='POST', format='multipart', data=file_data
        )
        self.assertEqual(response.status_code, 201, msg=response.data)
        new_file = File.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_file)
        self.assertNotEqual(new_file.file.file.size, 0)
        expected = {
            **file_data,
            'owner': str(self.user.sodar_uuid),
            'project': str(self.project.sodar_uuid),
            'public_url': self.file_data['public_url'],
            'secret': new_file.secret,
            'date_modified': self.get_drf_datetime(new_file.date_modified),
            'sodar_uuid': str(new_file.sodar_uuid),
        }
        expected.pop('file')
        self.assertEqual(json.loads(response.content), expected)

    def test_post_create_category(self):
        """Test POST to create file in category (should fail)"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_list_create',
                kwargs={'project': category.sodar_uuid},
            ),
            method='POST',
            format='multipart',
            data=self.file_data,
        )
        self.assertEqual(response.status_code, 403, msg=response.data)
        self.assertEqual(
            str(response.data['detail']),
            INVALID_PROJECT_TYPE_MSG.format(project_type=PROJECT_TYPE_CATEGORY),
        )


class TestFileRetrieveUpdateDestroyAPIView(FilesfoldersAPIViewTestBase):
    """Tests for FileRetrieveUpdateDestroyAPIView"""

    def setUp(self):
        super().setUp()
        self.file_data = {
            'name': 'UPDATED File',
            'flag': 'FLAG',
            'description': 'UPDATED description',
            'secret': 'foo',
            'public_url': False,
            'file': open(ZIP_PATH_NO_FILES, 'rb'),
        }
        self.url = reverse(
            'filesfolders:api_file_retrieve_update_destroy',
            kwargs={'file': self.file.sodar_uuid},
        )

    def tearDown(self):
        self.file_data['file'].close()
        super().tearDown()

    def test_get_retrieve(self):
        """Test FileRetrieveUpdateDestroyAPIView GET to retrieve file"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.file.name,
            'folder': None,
            'owner': str(self.file.owner.sodar_uuid),
            'project': str(self.file.project.sodar_uuid),
            'flag': self.file.flag,
            'description': self.file.description,
            'public_url': self.file.public_url,
            'secret': self.file.secret,
            'date_modified': self.get_drf_datetime(self.file.date_modified),
            'sodar_uuid': str(self.file.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_retrieve_update_destroy',
                kwargs={'file': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_put_update(self):
        """Test PUT to update file"""
        response = self.request_knox(
            self.url, method='PUT', format='multipart', data=self.file_data
        )
        self.assertEqual(response.status_code, 200, msg=response.data)
        old_secret = self.file.secret
        self.file.refresh_from_db()
        self.assertEqual(self.file.name, self.file_data['name'])
        self.assertEqual(self.file.flag, self.file_data['flag'])
        self.assertEqual(self.file.description, self.file_data['description'])
        self.assertNotEqual(
            self.file.secret,
            old_secret,
            msg='Secret should change when public_url flag changes',
        )
        expected = {
            **self.file_data,
            'folder': None,
            'owner': str(self.file.owner.sodar_uuid),
            'project': str(self.file.project.sodar_uuid),
            'public_url': self.file_data['public_url'],
            'secret': self.file.secret,
            'date_modified': self.get_drf_datetime(self.file.date_modified),
            'sodar_uuid': str(self.file.sodar_uuid),
        }
        expected.pop('file')
        self.assertEqual(json.loads(response.content), expected)

    def test_delete(self):
        """Test DELETE"""
        response = self.request_knox(self.url, method='DELETE')
        self.assertEqual(response.status_code, 204, msg=response.data)
        self.assertIsNone(response.data)
        with self.assertRaises(File.DoesNotExist):
            File.objects.get(
                project=self.project, sodar_uuid=self.file.sodar_uuid
            )


class TestFileServeAPIView(FilesfoldersAPIViewTestBase):
    """Tests for FileServeAPIView"""

    def test_get(self):
        """Test FileServeAPIView GET to download file"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_serve',
                kwargs={'file': self.file.sodar_uuid},
            )
        )
        expected = b'content'
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(response.content, expected)

    def test_get_not_found(self):
        """Test GET with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_file_serve',
                kwargs={'file': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)


class TestHyperLinkListCreateAPIView(FilesfoldersAPIViewTestBase):
    """Tests for HyperLinkListCreateAPIView"""

    def setUp(self):
        super().setUp()
        self.hyperlink_data = {
            'name': 'New HyperLink',
            'flag': 'IMPORTANT',
            'description': 'HyperLink\'s description',
            'url': 'http://www.cubi.bihealth.org',
        }
        self.url = reverse(
            'filesfolders:api_hyperlink_list_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get_list(self):
        """Test HyperLinkListCreateAPIView GET to list hyperlinks"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.hyperlink.name,
            'folder': None,
            'owner': str(self.hyperlink.owner.sodar_uuid),
            'project': str(self.hyperlink.project.sodar_uuid),
            'flag': self.hyperlink.flag,
            'description': self.hyperlink.description,
            'url': self.hyperlink.url,
            'date_modified': self.get_drf_datetime(
                self.hyperlink.date_modified
            ),
            'sodar_uuid': str(self.hyperlink.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), [expected])

    def test_get_pagination(self):
        """Test GET with pagination"""
        url = self.url + '?page=1'
        response = self.request_knox(url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'name': self.hyperlink.name,
                    'folder': None,
                    'owner': str(self.hyperlink.owner.sodar_uuid),
                    'project': str(self.hyperlink.project.sodar_uuid),
                    'flag': self.hyperlink.flag,
                    'description': self.hyperlink.description,
                    'url': self.hyperlink.url,
                    'date_modified': self.get_drf_datetime(
                        self.hyperlink.date_modified
                    ),
                    'sodar_uuid': str(self.hyperlink.sodar_uuid),
                }
            ],
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_root(self):
        """Test POST to create hyperlink in root"""
        response = self.request_knox(
            self.url, method='POST', data=self.hyperlink_data
        )
        self.assertEqual(response.status_code, 201, msg=response.data)
        new_link = HyperLink.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_link)
        expected = {
            **self.hyperlink_data,
            'folder': None,
            'owner': str(self.user.sodar_uuid),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_link.date_modified),
            'sodar_uuid': str(new_link.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_folder(self):
        """Test POST to create hyperlink under folder"""
        hyperlink_data = {
            **self.hyperlink_data,
            'folder': str(self.folder.sodar_uuid),
        }
        response = self.request_knox(
            self.url, method='POST', data=hyperlink_data
        )
        self.assertEqual(response.status_code, 201, msg=response.data)
        new_link = HyperLink.objects.filter(
            sodar_uuid=response.data['sodar_uuid']
        ).first()
        self.assertIsNotNone(new_link)
        expected = {
            **hyperlink_data,
            'owner': str(self.user.sodar_uuid),
            'project': str(self.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(new_link.date_modified),
            'sodar_uuid': str(new_link.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_post_category(self):
        """Test POST to create hyperlink in category (should fail)"""
        category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.make_assignment(category, self.user, self.role_owner)
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_list_create',
                kwargs={'project': category.sodar_uuid},
            ),
            method='POST',
            data=self.hyperlink_data,
        )
        self.assertEqual(response.status_code, 403, msg=response.data)
        self.assertEqual(
            str(response.data['detail']),
            INVALID_PROJECT_TYPE_MSG.format(project_type=PROJECT_TYPE_CATEGORY),
        )


class TestHyperLinkRetrieveUpdateDestroyAPIView(FilesfoldersAPIViewTestBase):
    """Tests for HyperLinkRetrieveUpdateDestroyAPIView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:api_hyperlink_retrieve_update_destroy',
            kwargs={'hyperlink': self.hyperlink.sodar_uuid},
        )

    def test_get_retrieve(self):
        """Test HyperLinkRetrieveUpdateDestroyAPIView to retrieve hyperlink"""
        response = self.request_knox(self.url)
        self.assertEqual(response.status_code, 200, msg=response.data)
        expected = {
            'name': self.hyperlink.name,
            'folder': None,
            'owner': str(self.hyperlink.owner.sodar_uuid),
            'project': str(self.hyperlink.project.sodar_uuid),
            'flag': self.hyperlink.flag,
            'description': self.hyperlink.description,
            'url': self.hyperlink.url,
            'date_modified': self.get_drf_datetime(
                self.hyperlink.date_modified
            ),
            'sodar_uuid': str(self.hyperlink.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        response = self.request_knox(
            reverse(
                'filesfolders:api_hyperlink_retrieve_update_destroy',
                kwargs={'hyperlink': INVALID_UUID},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_put_update(self):
        """Test PUT to update hyperlink"""
        hyperlink_data = {
            'name': 'UPDATED HyperLink',
            'flag': 'FLAG',
            'description': 'UPDATED Description',
            'url': 'http://www.bihealth.org',
        }
        response = self.request_knox(
            self.url, method='PUT', data=hyperlink_data
        )
        self.assertEqual(response.status_code, 200, msg=response.data)
        self.hyperlink.refresh_from_db()
        self.assertEqual(self.hyperlink.name, hyperlink_data['name'])
        self.assertEqual(self.hyperlink.flag, hyperlink_data['flag'])
        self.assertEqual(
            self.hyperlink.description, hyperlink_data['description']
        )
        expected = {
            **hyperlink_data,
            'folder': None,
            'owner': str(self.hyperlink.owner.sodar_uuid),
            'project': str(self.hyperlink.project.sodar_uuid),
            'date_modified': self.get_drf_datetime(
                self.hyperlink.date_modified
            ),
            'sodar_uuid': str(self.hyperlink.sodar_uuid),
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_delete(self):
        """Test DELETE"""
        response = self.request_knox(self.url, method='DELETE')
        self.assertEqual(response.status_code, 204, msg=response.data)
        self.assertIsNone(response.data)
