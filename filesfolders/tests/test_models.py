"""Tests for models in the filesfolders app"""

import base64

from typing import Optional

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import model_to_dict

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import Project, SODARUser, SODAR_CONSTANTS
from projectroles.tests.test_models import ProjectMixin

from filesfolders.models import File, FileData, Folder, HyperLink


# SODAR constants
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
PROJECT_NAME = 'Test Project'
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'


# Helper mixins ----------------------------------------------------------


class FileMixin:
    """Helper mixin for File creation"""

    @classmethod
    def make_file(
        cls,
        name: str,
        file_name: str,
        file_content: bytes,
        project: Project,
        folder: Optional[Folder],
        owner: SODARUser,
        description: str,
        public_url: bool,
        secret: str,
        flag: Optional[str] = None,
    ) -> File:
        """Create File object"""
        values = {
            'name': name,
            'file': SimpleUploadedFile(file_name, file_content),
            'project': project,
            'folder': folder,
            'owner': owner,
            'description': description,
            'public_url': public_url,
            'secret': secret,
            'flag': flag,
        }
        return File.objects.create(**values)


class FolderMixin:
    """Helper mixin for Folder creation"""

    @classmethod
    def make_folder(
        cls,
        name: str,
        project: Project,
        folder: Optional[Folder],
        owner: SODARUser,
        description: str,
        flag: Optional[str] = None,
    ) -> Folder:
        """Create Folder object"""
        values = {
            'name': name,
            'project': project,
            'folder': folder,
            'owner': owner,
            'description': description,
            'flag': flag,
        }
        return Folder.objects.create(**values)


class HyperLinkMixin:
    """Helper mixin for HyperLink creation"""

    @classmethod
    def make_hyperlink(
        cls,
        name: str,
        url: str,
        project: Project,
        folder: Optional[Folder],
        owner: SODARUser,
        description: str,
        flag: Optional[str] = None,
    ) -> HyperLink:
        """Create HyperLink object"""
        values = {
            'name': name,
            'url': url,
            'project': project,
            'folder': folder,
            'owner': owner,
            'description': description,
            'flag': flag,
        }
        return HyperLink.objects.create(**values)


# Test classes -----------------------------------------------------------


class TestFolder(FolderMixin, ProjectMixin, HyperLinkMixin, TestCase):
    """Tests for Folder"""

    def setUp(self):
        # Make owner user
        self.user_owner = self.make_user('owner')
        # Make project
        self.project = self.make_project(
            PROJECT_NAME, PROJECT_TYPE_PROJECT, None
        )
        # Make folder
        self.folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
        )

    def test_initialization(self):
        expected = {
            'id': self.folder.pk,
            'name': 'folder',
            'project': self.project.pk,
            'folder': None,
            'owner': self.user_owner.pk,
            'description': 'description',
            'flag': None,
            'sodar_uuid': self.folder.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.folder), expected)

    def test_find_name(self):
        """Test FilesfoldersManager find() with Folder name"""
        objects = Folder.objects.find(['folder'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.folder)

    def test_find_desc(self):
        """Test FilesfoldersManager find() with Folder description"""
        objects = Folder.objects.find(['description'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.folder)

    def test_find_uuid(self):
        """Test FilesfoldersManager find() with Folder UUID"""
        objects = Folder.objects.find(str(self.folder.sodar_uuid))
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.folder)

    def test_find_fail(self):
        """Test FilesfoldersManager find() with a non-existing Folder"""
        objects = Folder.objects.find(['Jaix1azu'])
        self.assertEqual(len(objects), 0)

    def test__str__(self):
        expected = f'{PROJECT_NAME}: root/folder'
        self.assertEqual(str(self.folder), expected)

    def test__repr__(self):
        expected = f"Folder('{PROJECT_NAME}', 'folder', '/')"
        self.assertEqual(repr(self.folder), expected)

    def test_create_subfolder(self):
        """Test subfolder creation"""
        subfolder = self.make_folder(
            name='subfolder',
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='',
        )
        expected = {
            'id': subfolder.pk,
            'name': 'subfolder',
            'project': self.project.pk,
            'folder': self.folder.pk,
            'owner': self.user_owner.pk,
            'description': '',
            'flag': None,
            'sodar_uuid': subfolder.sodar_uuid,
        }
        self.assertEqual(model_to_dict(subfolder), expected)

    def test_get_path(self):
        """Test get_irods_path() in Folder"""
        self.assertEqual(self.folder.get_path(), 'root/folder/')

    def test_get_path_subfolder(self):
        """Test get_irods_path() in Folder for a subfolder"""
        subfolder = self.make_folder(
            name='subfolder',
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='',
        )
        self.assertEqual(subfolder.get_path(), 'root/folder/subfolder/')

    def test_is_empty(self):
        """Test is_empty() in Folder for an empty folder"""
        self.assertEqual(self.folder.is_empty(), True)

    def test_is_empty_nonempty(self):
        """Test is_empty() in Folder for a non-empty folder"""
        self.hyperlink = self.make_hyperlink(
            name='Link',
            url='http://www.google.com/',
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='',
        )
        self.assertEqual(self.folder.is_empty(), False)

    def test_has_in_path(self):
        """Test has_in_path() in Folder"""
        subfolder = self.make_folder(
            name='subfolder',
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='',
        )
        self.assertEqual(subfolder.has_in_path(self.folder), True)

    def test_has_in_path_false(self):
        """Test has_in_path() in Folder with expected false result"""
        subfolder = self.make_folder(
            name='subfolder',
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='',
        )
        self.assertEqual(self.folder.has_in_path(subfolder), False)


class TestFile(FileMixin, FolderMixin, ProjectMixin, TestCase):
    """Tests for File"""

    def setUp(self):
        # Make owner user
        self.user_owner = self.make_user('owner')
        # Make project
        self.project = self.make_project(
            PROJECT_NAME, PROJECT_TYPE_PROJECT, None
        )
        # Make folder
        self.folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
        )
        self.file_content = bytes('content'.encode('utf-8'))
        # Make file
        self.file = self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='description',
            public_url=True,
            secret=SECRET,
        )

    def test_initialization(self):
        expected = {
            'id': self.file.pk,
            'name': 'file.txt',
            'file': self.file.file,
            'project': self.project.pk,
            'folder': self.folder.pk,
            'owner': self.user_owner.pk,
            'description': 'description',
            'public_url': True,
            'secret': SECRET,
            'flag': None,
            'sodar_uuid': self.file.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.file), expected)

    def test_find_name(self):
        """Test FilesfoldersManager find() with File name"""
        objects = File.objects.find(['file.txt'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.file)

    def test_find_desc(self):
        """Test FilesfoldersManager find() with File description"""
        objects = File.objects.find(['description'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.file)

    def test_find_uuid(self):
        """Test FilesfoldersManager find() with File UUID"""
        objects = File.objects.find(str(self.file.sodar_uuid))
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.file)

    def test_find_fail(self):
        """Test FilesfoldersManager find() with a non-existing File"""
        objects = File.objects.find(['Jaix1azu'])
        self.assertEqual(len(objects), 0)

    def test__str__(self):
        expected = '{}: root/{}/{}'.format(
            PROJECT_NAME, self.folder.name, self.file.name
        )
        self.assertEqual(str(self.file), expected)

    def test__repr__(self):
        expected = "File('{}', '{}', {})".format(
            PROJECT_NAME, self.file.name, self.folder.__repr__()
        )
        self.assertEqual(repr(self.file), expected)

    def test_file_access(self):
        """Test file can be accessed in database after creation"""
        file_data = FileData.objects.get(file_name=self.file.file.name)
        expected = {
            'id': file_data.pk,
            'file_name': 'filesfolders.FileData/bytes/file_name/'
            'content_type/file.txt',
            'content_type': 'text/plain',
            'bytes': base64.b64encode(self.file_content).decode('utf-8'),
        }
        self.assertEqual(model_to_dict(file_data), expected)

    def test_file_deletion(self):
        """Test file is removed from database after deletion"""
        self.assertEqual(FileData.objects.all().count(), 1)
        self.file.delete()
        self.assertEqual(FileData.objects.all().count(), 0)


class TestHyperLink(
    FileMixin, FolderMixin, ProjectMixin, HyperLinkMixin, TestCase
):
    """Tests for HyperLink"""

    def setUp(self):
        # Make owner user
        self.user_owner = self.make_user('owner')
        # Make project
        self.project = self.make_project(
            PROJECT_NAME, PROJECT_TYPE_PROJECT, None
        )
        # Make folder
        self.folder = self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        # Make hyperlink
        self.hyperlink = self.make_hyperlink(
            name='Link',
            url='http://www.google.com/',
            project=self.project,
            folder=self.folder,
            owner=self.user_owner,
            description='description',
        )

    def test_initialization(self):
        expected = {
            'id': self.hyperlink.pk,
            'name': 'Link',
            'url': 'http://www.google.com/',
            'project': self.project.pk,
            'folder': self.folder.pk,
            'owner': self.user_owner.pk,
            'description': 'description',
            'flag': None,
            'sodar_uuid': self.hyperlink.sodar_uuid,
        }
        self.assertEqual(model_to_dict(self.hyperlink), expected)

    def test__str__(self):
        expected = '{}: {} / {}'.format(
            PROJECT_NAME, self.folder.name, self.hyperlink.name
        )
        self.assertEqual(str(self.hyperlink), expected)

    def test__repr__(self):
        expected = "HyperLink('{}', '{}', {})".format(
            PROJECT_NAME, self.hyperlink.name, self.folder.__repr__()
        )
        self.assertEqual(repr(self.hyperlink), expected)

    def test_find_name(self):
        """Test FilesfoldersManager find() with HyperLink name"""
        objects = HyperLink.objects.find(['Link'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.hyperlink)

    def test_find_desc(self):
        """Test FilesfoldersManager find() with HyperLink description"""
        objects = HyperLink.objects.find(['description'])
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.hyperlink)

    def test_find_uuid(self):
        """Test FilesfoldersManager find() with HyperLink UUID"""
        objects = HyperLink.objects.find(str(self.hyperlink.sodar_uuid))
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0], self.hyperlink)

    def test_find_fail(self):
        """Test FilesfoldersManager find() with a non-existing HyperLink"""
        objects = HyperLink.objects.find(['Jaix1azu'])
        self.assertEqual(len(objects), 0)
