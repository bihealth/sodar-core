"""Tests for views in the filesfolders app"""

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)
from projectroles.app_settings import AppSettingAPI

from filesfolders.models import File, Folder, HyperLink
from filesfolders.tests.test_models import (
    FolderMixin,
    FileMixin,
    HyperLinkMixin,
)
from filesfolders.utils import build_public_url


app_settings = AppSettingAPI()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME = 'filesfolders'
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'
TEST_DATA_PATH = os.path.dirname(__file__) + '/data/'
ZIP_PATH = TEST_DATA_PATH + 'unpack_test.zip'
ZIP_PATH_NO_FILES = TEST_DATA_PATH + 'no_files.zip'
INVALID_UUID = '11111111-1111-1111-1111-111111111111'
EMPTY_FILE_MSG = 'The submitted file is empty.'


class FilesfoldersViewTestMixin(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    FileMixin,
    FolderMixin,
    HyperLinkMixin,
):
    def setUp(self):
        self.req_factory = RequestFactory()
        # Init roles
        self.init_roles()
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        # Init project and owner role
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, None
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Change public link setting from default
        app_settings.set(
            APP_NAME, 'allow_public_links', True, project=self.project
        )
        # Init file content
        self.file_content = bytes('content'.encode('utf-8'))
        self.file_content_alt = bytes('alt content'.encode('utf-8'))
        self.file_content_empty = bytes(''.encode('utf-8'))

        # Init file
        self.file = self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
            public_url=True,
            secret=SECRET,
        )
        # Init folder
        self.folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )
        # Init link
        self.hyperlink = self.make_hyperlink(
            name='Link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )


class ViewTestBase(FilesfoldersViewTestMixin, TestCase):
    """Base class for filesfolders view testing"""


# Project Files View -----------------------------------------------------------


class TestProjectFileView(ViewTestBase):
    """Tests for ProjectFileView"""

    def test_get_root(self):
        """Test ProjectFileView GET in root"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:list',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        self.assertIsNotNone(response.context['folders'])
        self.assertIsNotNone(response.context['files'])
        self.assertIsNotNone(response.context['links'])
        self.assertEqual(response.context['allow_public_links'], True)

    def test_get_invalid_uuid(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:list',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_get_folder(self):
        """Test GET under folder"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:list',
                    kwargs={'folder': self.folder.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        self.assertIsNotNone(response.context['folder_breadcrumb'])
        self.assertIsNotNone(response.context['files'])
        self.assertIsNotNone(response.context['links'])

    def test_get_readme_txt(self):
        """Test GET with plaintext readme file"""
        self.readme_file = self.make_file(
            name='readme.txt',
            file_name='readme.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
            public_url=False,
            secret='xxxxxxxxx',
        )
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:list',
                    kwargs={'project': self.project.sodar_uuid},
                )
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['readme_name'], 'readme.txt')
        self.assertEqual(response.context['readme_data'], self.file_content)
        self.assertEqual(response.context['readme_mime'], 'text/plain')


# Folder Views -----------------------------------------------------------------


class TestFolderCreateView(ViewTestBase):
    """Tests for FolderCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:folder_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_folder = reverse(
            'filesfolders:folder_create',
            kwargs={'folder': self.folder.sodar_uuid},
        )

    def test_get(self):
        """Test FolderCreateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)

    def test_get_invalid_uuid(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:folder_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_get_folder(self):
        """Test GET under folder"""
        with self.login(self.user):
            response = self.client.get(self.url_folder)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['folder'], self.folder)

    def test_post(self):
        """Test POST to create folder"""
        self.assertEqual(Folder.objects.all().count(), 1)
        post_data = {
            'name': 'new_folder',
            'folder': '',
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(Folder.objects.all().count(), 2)

    def test_post_folder(self):
        """Test POST under folder"""
        self.assertEqual(Folder.objects.all().count(), 1)
        post_data = {
            'name': 'new_folder',
            'folder': self.folder.sodar_uuid,
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'folder': self.folder.sodar_uuid},
            ),
        )
        self.assertEqual(Folder.objects.all().count(), 2)

    def test_post_existing(self):
        """Test POST with existing folder (should fail)"""
        self.assertEqual(Folder.objects.all().count(), 1)
        post_data = {
            'name': 'folder',
            'folder': '',
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Folder.objects.all().count(), 1)


class TestFolderUpdateView(ViewTestBase):
    """Tests for FolderUpdateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:folder_update',
            kwargs={'item': self.folder.sodar_uuid},
        )

    def test_get(self):
        """Test FolderUpdateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.folder)

    def test_get_invalid_uuid(self):
        """Test GET with invalid folder UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:folder_update',
                    kwargs={'item': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to update folder"""
        self.assertEqual(Folder.objects.all().count(), 1)
        post_data = {
            'name': 'renamed_folder',
            'folder': '',
            'description': 'updated description',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(Folder.objects.all().count(), 1)
        self.folder.refresh_from_db()
        self.assertEqual(self.folder.name, 'renamed_folder')
        self.assertEqual(self.folder.description, 'updated description')

    def test_post_existing(self):
        """Test POST with existing folder name (should fail)"""
        self.make_folder(
            name='folder2',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )
        self.assertEqual(Folder.objects.all().count(), 2)

        post_data = {
            'name': 'folder2',
            'folder': '',
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Folder.objects.all().count(), 2)
        self.folder.refresh_from_db()
        self.assertEqual(self.folder.name, 'folder')


class TestFolderDeleteView(ViewTestBase):
    """Tests for FolderDeleteView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:folder_delete',
            kwargs={'item': self.folder.sodar_uuid},
        )

    def test_get(self):
        """Test FolderDeleteView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.folder)

    def test_get_invalid_uuid(self):
        """Test GET with invalid folder UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:folder_delete',
                    kwargs={'item': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to delete folder"""
        self.assertEqual(Folder.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(Folder.objects.all().count(), 0)


# File Views -------------------------------------------------------------------


class TestFileCreateView(ViewTestBase):
    """Tests for FileCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:file_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_folder = reverse(
            'filesfolders:file_create',
            kwargs={'folder': self.folder.sodar_uuid},
        )
        self.url_list = reverse(
            'filesfolders:list',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_list_folder = reverse(
            'filesfolders:list',
            kwargs={'folder': self.folder.sodar_uuid},
        )

    def test_get(self):
        """Test FileCreateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)

    def test_get_folder(self):
        """Test GET under folder"""
        with self.login(self.user):
            response = self.client.get(self.url_folder)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['folder'], self.folder)

    def test_get_invalid_uuid(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:file_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to create file"""
        self.assertEqual(File.objects.all().count(), 1)
        post_data = {
            'name': 'new_file.txt',
            'file': SimpleUploadedFile('new_file.txt', self.file_content),
            'folder': '',
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_list)
        self.assertEqual(File.objects.all().count(), 2)

    def test_post_empty(self):
        """Test POST with empty file (should fail)"""
        self.assertEqual(File.objects.all().count(), 1)
        post_data = {
            'name': 'new_file.txt',
            'file': SimpleUploadedFile(
                'empty_file.txt', self.file_content_empty
            ),
            'folder': '',
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(EMPTY_FILE_MSG, response.content.decode('utf-8'))
        self.assertEqual(File.objects.all().count(), 1)

    def test_post_folder(self):
        """Test POST under folder"""
        self.assertEqual(File.objects.all().count(), 1)
        post_data = {
            'name': 'new_file.txt',
            'file': SimpleUploadedFile('new_file.txt', self.file_content),
            'folder': self.folder.sodar_uuid,
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url_folder, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_list_folder)
        self.assertEqual(File.objects.all().count(), 2)

    def test_post_existing(self):
        """Test POST with existing file name (should fail)"""
        self.assertEqual(File.objects.all().count(), 1)
        post_data = {
            'name': 'file.txt',
            'file': SimpleUploadedFile('file.txt', self.file_content_alt),
            'folder': '',
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.all().count(), 1)

    def test_post_unpack_archive(self):
        """Test POST with zip archive to be unpacked"""
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(Folder.objects.all().count(), 1)

        with open(ZIP_PATH, 'rb') as zip_file:
            post_data = {
                'name': 'unpack_test.zip',
                'file': zip_file,
                'folder': '',
                'description': '',
                'flag': '',
                'public_url': False,
                'unpack_archive': True,
            }
            with self.login(self.user):
                response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_list)
        self.assertEqual(File.objects.all().count(), 3)
        self.assertEqual(Folder.objects.all().count(), 3)

        new_file1 = File.objects.get(name='zip_test1.txt')
        new_file2 = File.objects.get(name='zip_test2.txt')
        new_folder1 = Folder.objects.get(name='dir1')
        new_folder2 = Folder.objects.get(name='dir2')
        self.assertEqual(new_file1.folder, new_folder1)
        self.assertEqual(new_file2.folder, new_folder2)
        self.assertEqual(new_folder2.folder, new_folder1)

    def test_post_unpack_archive_overwrite(self):
        """Test POST to unpack archive with existing file (should fail)"""
        ow_folder = self.make_folder(
            name='dir1',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )
        self.make_file(
            name='zip_test1.txt',
            file_name='zip_test1.txt',
            file_content=self.file_content,
            project=self.project,
            folder=ow_folder,
            owner=self.user,
            description='',
            public_url=False,
            secret='xxxxxxxxx',
        )
        self.assertEqual(File.objects.all().count(), 2)
        self.assertEqual(Folder.objects.all().count(), 2)

        with open(ZIP_PATH, 'rb') as zip_file:
            post_data = {
                'name': 'unpack_test.zip',
                'file': zip_file,
                'folder': '',
                'description': '',
                'flag': '',
                'public_url': False,
                'unpack_archive': True,
            }
            with self.login(self.user):
                response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.all().count(), 2)
        self.assertEqual(Folder.objects.all().count(), 2)

    def test_post_unpack_archive_empty(self):
        """Test POST with empty archive (should fail)"""
        with open(ZIP_PATH_NO_FILES, 'rb') as zip_file:
            post_data = {
                'name': 'no_files.zip',
                'file': zip_file,
                'folder': '',
                'description': '',
                'flag': '',
                'public_url': False,
                'unpack_archive': True,
            }
            with self.login(self.user):
                response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_post_archive_existing(self):
        """Test POST to upload archive with existing file (no unpack)"""
        ow_folder = self.make_folder(
            name='dir1',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )
        self.make_file(
            name='zip_test1.txt',
            file_name='zip_test1.txt',
            file_content=self.file_content,
            project=self.project,
            folder=ow_folder,
            owner=self.user,
            description='',
            public_url=False,
            secret='xxxxxxxxx',
        )
        self.assertEqual(File.objects.all().count(), 2)
        self.assertEqual(Folder.objects.all().count(), 2)

        with open(ZIP_PATH, 'rb') as zip_file:
            post_data = {
                'name': 'unpack_test.zip',
                'file': zip_file,
                'folder': '',
                'description': '',
                'flag': '',
                'public_url': False,
                'unpack_archive': False,
            }
            with self.login(self.user):
                response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(File.objects.all().count(), 3)
        self.assertEqual(Folder.objects.all().count(), 2)


class TestFileUpdateView(ViewTestBase):
    """Tests for FileUpdateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:file_update',
            kwargs={'item': self.file.sodar_uuid},
        )
        self.url_list = reverse(
            'filesfolders:list',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_list_folder = reverse(
            'filesfolders:list',
            kwargs={'folder': self.folder.sodar_uuid},
        )

    def test_get(self):
        """Test FileUpdateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.file)

    def test_get_invalid_uuid(self):
        """Test GET with invalid file UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:file_update',
                    kwargs={'item': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to update file"""
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(self.file.file.read(), self.file_content)

        post_data = {
            'name': 'file.txt',
            'file': SimpleUploadedFile('file.txt', self.file_content_alt),
            'folder': '',
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_list)
        self.assertEqual(File.objects.all().count(), 1)
        self.file.refresh_from_db()
        self.assertEqual(self.file.file.read(), self.file_content_alt)

    def test_post_empty(self):
        """Test POST with empty file content"""
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(self.file.file.read(), self.file_content)

        post_data = {
            'name': 'file.txt',
            'file': SimpleUploadedFile('file.txt', self.file_content_empty),
            'folder': '',
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(EMPTY_FILE_MSG, response.content.decode('utf-8'))
        self.assertEqual(File.objects.all().count(), 1)
        self.file.refresh_from_db()
        self.assertEqual(self.file.file.read(), self.file_content)

    def test_post_existing(self):
        """Test POST with existing file name (should fail)"""
        self.make_file(
            name='file2.txt',
            file_name='file2.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
            public_url=True,
            secret='abc123',
        )
        self.assertEqual(File.objects.all().count(), 2)

        post_data = {
            'name': 'file2.txt',
            'file': SimpleUploadedFile('file2.txt', self.file_content_alt),
            'folder': '',
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.all().count(), 2)
        self.file.refresh_from_db()
        self.assertEqual(self.file.file.read(), self.file_content)

    def test_post_move_folder(self):
        """Test POST to move file to another folder"""
        post_data = {
            'name': 'file.txt',
            'folder': self.folder.sodar_uuid,
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url_list_folder)
        self.file.refresh_from_db()
        self.assertEqual(self.file.folder, self.folder)

    def test_post_move_folder_existing(self):
        """Test POST to overwrite file in another folder (should fail)"""
        # Create file with same name in the target folder
        self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content_alt,
            project=self.project,
            folder=self.folder,
            owner=self.user,
            description='',
            public_url=True,
            secret='aaaaaaaaa',
        )

        post_data = {
            'name': 'file.txt',
            'folder': self.folder.pk,
            'description': '',
            'flag': '',
            'public_url': False,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(File.objects.all().count(), 2)
        self.file.refresh_from_db()
        self.assertEqual(self.file.folder, None)


class TestFileDeleteView(ViewTestBase):
    """Tests for FileDeleteView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:file_delete',
            kwargs={'item': self.file.sodar_uuid},
        )

    def test_get(self):
        """Test FileDeleteView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.file)

    def test_get_invalid_uuid(self):
        """Test GET with invalid file UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:file_delete',
                    kwargs={'item': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to delete file"""
        self.assertEqual(File.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(File.objects.all().count(), 0)


class TestFileServeView(ViewTestBase):
    """Tests for FileServeView"""

    def test_get(self):
        """Test FileServeView GET"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:file_serve',
                    kwargs={
                        'file': self.file.sodar_uuid,
                        'file_name': self.file.name,
                    },
                )
            )
        self.assertEqual(response.status_code, 200)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:file_serve',
                    kwargs={
                        'file': INVALID_UUID,
                        'file_name': self.file.name,
                    },
                )
            )
        self.assertEqual(response.status_code, 404)


class TestFileServePublicView(ViewTestBase):
    """Tests for FileServePublicView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:file_serve_public',
            kwargs={'secret': SECRET, 'file_name': self.file.name},
        )

    def test_get(self):
        """Test FileServePublicView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_link_disabled(self):
        """Test GET with disabled public link setting (should fail)"""
        app_settings.set(
            APP_NAME, 'allow_public_links', False, project=self.project
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_get_public_url_disabled(self):
        """Test GET with file public_url set to False (should fail)"""
        self.file.public_url = False
        self.file.save()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

    def test_get_deleted_file(self):
        """Test GET with deleted file (should fail)"""
        self.file.delete()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)


class TestFilePublicLinkView(ViewTestBase):
    """Tests for FilePublicLinkView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:file_public_link',
            kwargs={'file': self.file.sodar_uuid},
        )

    def test_get(self):
        """Test FilePublicLinkView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['public_url'],
            build_public_url(
                self.file,
                self.req_factory.get(
                    'file_public_link',
                    kwargs={'file': self.file.sodar_uuid},
                ),
            ),
        )

    def test_get_invalid_uuid(self):
        """Test GET with invalid file UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:file_public_link',
                    kwargs={'file': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_get_public_links_disabled(self):
        """Test GET with disabled public linking (should fail)"""
        app_settings.set(
            APP_NAME, 'allow_public_links', False, project=self.project
        )
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_get_deleted_file(self):
        """Test GET with deleted file (should fail)"""
        self.file.delete()
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)


# HyperLink Views --------------------------------------------------------------


class TestHyperLinkCreateView(ViewTestBase):
    """Tests for HyperLinkCreateView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.url_folder = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'folder': self.folder.sodar_uuid},
        )

    def test_get(self):
        """Test HyperLinkCreateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)

    def test_get_invalid_uuid(self):
        """Test GET with invalid project UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:hyperlink_create',
                    kwargs={'project': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_get_folder(self):
        """Test GET under folder"""
        with self.login(self.user):
            response = self.client.get(self.url_folder)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['folder'], self.folder)

    def test_post(self):
        """Test POST to create hyperlink"""
        self.assertEqual(HyperLink.objects.all().count(), 1)
        post_data = {
            'name': 'new link',
            'url': 'http://link.com',
            'folder': '',
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(HyperLink.objects.all().count(), 2)

    def test_post_folder(self):
        """Test POST under folder"""
        self.assertEqual(HyperLink.objects.all().count(), 1)
        post_data = {
            'name': 'new link',
            'url': 'http://link.com',
            'folder': self.folder.sodar_uuid,
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url_folder, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'folder': self.folder.sodar_uuid},
            ),
        )
        self.assertEqual(HyperLink.objects.all().count(), 2)

    def test_post_existing(self):
        """Test POST with existing file (should fail)"""
        self.assertEqual(HyperLink.objects.all().count(), 1)
        post_data = {
            'name': 'Link',
            'url': 'http://google.com',
            'folder': '',
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(HyperLink.objects.all().count(), 1)


class TestHyperLinkUpdateView(ViewTestBase):
    """Tests for HyperLinkUpdateView("""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:hyperlink_update',
            kwargs={'item': self.hyperlink.sodar_uuid},
        )

    def test_get(self):
        """Test HyperLinkUpdateView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.hyperlink)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:hyperlink_update',
                    kwargs={'item': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to update hyperlink"""
        self.assertEqual(HyperLink.objects.all().count(), 1)
        post_data = {
            'name': 'Renamed Link',
            'url': 'http://updated.com',
            'folder': '',
            'description': 'updated description',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(HyperLink.objects.all().count(), 1)
        self.hyperlink.refresh_from_db()
        self.assertEqual(self.hyperlink.name, 'Renamed Link')
        self.assertEqual(self.hyperlink.url, 'http://updated.com')
        self.assertEqual(self.hyperlink.description, 'updated description')

    def test_post_existing(self):
        """Test POST with existing name (should fail)"""
        self.make_hyperlink(
            name='Link2',
            url='http://url2.com',
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
        )
        self.assertEqual(HyperLink.objects.all().count(), 2)

        post_data = {
            'name': 'Link2',
            'url': self.hyperlink.url,
            'folder': '',
            'description': '',
            'flag': '',
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(HyperLink.objects.all().count(), 2)
        self.hyperlink.refresh_from_db()
        self.assertEqual(self.hyperlink.name, 'Link')


class TestHyperLinkDeleteView(ViewTestBase):
    """Tests for HyperLinkDeleteView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:hyperlink_delete',
            kwargs={'item': self.hyperlink.sodar_uuid},
        )

    def test_get(self):
        """Test HyperLinkDeleteView GET"""
        with self.login(self.user):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], self.hyperlink)

    def test_get_invalid_uuid(self):
        """Test GET with invalid UUID"""
        with self.login(self.user):
            response = self.client.get(
                reverse(
                    'filesfolders:hyperlink_delete',
                    kwargs={'item': INVALID_UUID},
                )
            )
        self.assertEqual(response.status_code, 404)

    def test_post(self):
        """Test POST to delete hyperlink"""
        self.assertEqual(HyperLink.objects.all().count(), 1)
        with self.login(self.user):
            response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse(
                'filesfolders:list',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assertEqual(HyperLink.objects.all().count(), 0)


# Batch Editing View -----------------------------------------------------------


class TestBatchEditView(ViewTestBase):
    """Tests for BatchEditView"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:batch_edit',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get_delete(self):
        """Test BatchEditView GET with deleting"""
        post_data = {'batch-action': 'delete', 'user-confirmed': '0'}
        post_data[f'batch_item_File_{self.file.sodar_uuid}'] = 1
        post_data[f'batch_item_Folder_{self.folder.sodar_uuid}'] = 1
        post_data[f'batch_item_HyperLink_{self.hyperlink.sodar_uuid}'] = 1
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_get_move(self):
        """Test GET when moving"""
        post_data = {'batch-action': 'move', 'user-confirmed': '0'}
        post_data[f'batch_item_File_{self.file.sodar_uuid}'] = 1
        post_data[f'batch_item_HyperLink_{self.hyperlink.sodar_uuid}'] = 1
        with self.login(self.user):
            response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_post_delete(self):
        """Test POST for batch object deletion"""
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(Folder.objects.all().count(), 1)
        self.assertEqual(HyperLink.objects.all().count(), 1)

        post_data = {'batch-action': 'delete', 'user-confirmed': '1'}
        post_data[f'batch_item_File_{self.file.sodar_uuid}'] = 1
        post_data[f'batch_item_Folder_{self.folder.sodar_uuid}'] = 1
        post_data[f'batch_item_HyperLink_{self.hyperlink.sodar_uuid}'] = 1
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(File.objects.all().count(), 0)
        self.assertEqual(Folder.objects.all().count(), 0)
        self.assertEqual(HyperLink.objects.all().count(), 0)

    def test_post_delete_non_empty_folder(self):
        """Test POST for deletion with non-empty folder (should not be deleted)"""
        new_folder = self.make_folder(
            'new_folder', self.project, None, self.user, ''
        )
        self.make_file(
            name='new_file.txt',
            file_name='new_file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=new_folder,  # Set new folder as parent
            owner=self.user,
            description='',
            public_url=True,
            secret='7dqq83clo2iyhg29hifbor56og6911r6',
        )
        self.assertEqual(File.objects.all().count(), 2)
        self.assertEqual(Folder.objects.all().count(), 2)

        post_data = {'batch-action': 'delete', 'user-confirmed': '1'}
        post_data[f'batch_item_File_{self.file.sodar_uuid}'] = 1
        post_data[f'batch_item_Folder_{self.folder.sodar_uuid}'] = 1
        post_data[f'batch_item_HyperLink_{self.hyperlink.sodar_uuid}'] = 1
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        # The new folder and file should be left
        self.assertEqual(File.objects.all().count(), 1)
        self.assertEqual(Folder.objects.all().count(), 1)

    def test_post_move(self):
        """Test POST for batch object moving"""
        target_folder = self.make_folder(
            'target_folder', self.project, None, self.user, ''
        )
        post_data = {
            'batch-action': 'move',
            'user-confirmed': '1',
            'target-folder': target_folder.sodar_uuid,
            f'batch_item_File_{self.file.sodar_uuid}': 1,
            f'batch_item_Folder_{self.folder.sodar_uuid}': 1,
            f'batch_item_HyperLink_{self.hyperlink.sodar_uuid}': 1,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            File.objects.get(pk=self.file.pk).folder, target_folder
        )
        self.assertEqual(
            Folder.objects.get(pk=self.folder.pk).folder, target_folder
        )
        self.assertEqual(
            HyperLink.objects.get(pk=self.hyperlink.pk).folder, target_folder
        )

    def test_post_move_name_exists(self):
        """Test POST for moving with name existing in target (should not be moved)"""
        target_folder = self.make_folder(
            'target_folder', self.project, None, self.user, ''
        )
        self.make_file(
            name='file.txt',  # Same name as self.file
            file_name='file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=target_folder,  # New file is under target
            owner=self.user,
            description='',
            public_url=True,
            secret='7dqq83clo2iyhg29hifbor56og6911r6',
        )

        post_data = {
            'batch-action': 'move',
            'user-confirmed': '1',
            'target-folder': target_folder.sodar_uuid,
            f'batch_item_File_{self.file.sodar_uuid}': 1,
            f'batch_item_Folder_{self.folder.sodar_uuid}': 1,
            f'batch_item_HyperLink_{self.hyperlink.sodar_uuid}': 1,
        }
        with self.login(self.user):
            response = self.client.post(self.url, post_data)

        self.assertEqual(response.status_code, 302)
        # Not moved
        self.assertEqual(File.objects.get(pk=self.file.pk).folder, None)
        self.assertEqual(
            Folder.objects.get(pk=self.folder.pk).folder, target_folder
        )
        self.assertEqual(
            HyperLink.objects.get(pk=self.hyperlink.pk).folder, target_folder
        )
