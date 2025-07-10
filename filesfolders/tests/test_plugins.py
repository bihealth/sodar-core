"""Plugin tests for the filesfolders app"""

import uuid

from django.urls import reverse

from test_plus.test import TestCase

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import ProjectAppPluginPoint, PluginObjectLink
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
)
from projectroles.utils import build_secret

from filesfolders.tests.test_models import (
    FolderMixin,
    FileMixin,
    HyperLinkMixin,
)
from filesfolders.urls import urlpatterns


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
PLUGIN_NAME = 'filesfolders'
PLUGIN_TITLE = 'Files'
PLUGIN_URL_ID = 'filesfolders:list'
SETTING_KEY = 'allow_public_links'


class TestPlugin(
    ProjectMixin,
    RoleMixin,
    FolderMixin,
    FileMixin,
    HyperLinkMixin,
    RoleAssignmentMixin,
    TestCase,
):
    """Tests for filesfolders project app plugin"""

    def setUp(self):
        # Init superuser
        self.user = self.make_user('superuser')
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        # Init roles
        self.init_roles()
        # Init category and project
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.owner_as_cat = self.make_assignment(
            self.category, self.user, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Init file
        self.file_content = bytes('content'.encode('utf-8'))
        self.file = self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user,
            description='',
            public_url=True,
            secret=build_secret(),
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
        # Get plugin
        self.plugin = ProjectAppPluginPoint.get_plugin(PLUGIN_NAME)

    def test_plugin_retrieval(self):
        """Test retrieving ProjectAppPlugin from the database"""
        self.assertIsNotNone(self.plugin)
        self.assertEqual(self.plugin.get_model().name, PLUGIN_NAME)
        self.assertEqual(self.plugin.name, PLUGIN_NAME)
        self.assertEqual(self.plugin.get_model().title, PLUGIN_TITLE)
        self.assertEqual(self.plugin.title, PLUGIN_TITLE)
        self.assertEqual(self.plugin.entry_point_url_id, PLUGIN_URL_ID)

    def test_plugin_urls(self):
        """Test plugin URLs to ensure they're the same as in the app config"""
        self.assertEqual(self.plugin.urls, urlpatterns)

    def test_get_object_link_file(self):
        """Test get_object_link() for a File object"""
        url = reverse(
            'filesfolders:file_serve',
            kwargs={'file': self.file.sodar_uuid, 'file_name': self.file.name},
        )
        ret = self.plugin.get_object_link('File', self.file.sodar_uuid)
        self.assertIsInstance(ret, PluginObjectLink)
        self.assertEqual(ret.url, url)
        self.assertEqual(ret.name, self.file.name)
        self.assertEqual(ret.blank, True)

    def test_get_object_link_folder(self):
        """Test get_object_link() for a Folder object"""
        url = reverse(
            'filesfolders:list', kwargs={'folder': self.folder.sodar_uuid}
        )
        ret = self.plugin.get_object_link('Folder', self.folder.sodar_uuid)
        self.assertEqual(ret.url, url)
        self.assertEqual(ret.name, self.folder.name)
        self.assertEqual(ret.blank, False)

    def test_get_object_link_hyperlink(self):
        """Test get_object_link() for a HyperLink object"""
        ret = self.plugin.get_object_link(
            'HyperLink', self.hyperlink.sodar_uuid
        )
        self.assertEqual(ret.url, self.hyperlink.url)
        self.assertEqual(ret.name, self.hyperlink.name)
        self.assertEqual(ret.blank, True)

    def test_get_object_link_fail(self):
        """Test get_object_link() with a non-existent object"""
        self.assertEqual(
            self.plugin.get_object_link('File', uuid.uuid4()), None
        )

    def test_get_category_stats(self):
        """Test get_category_stats()"""
        ret = self.plugin.get_category_stats(self.category)
        self.assertEqual(len(ret), 1)
        self.assertIsInstance(ret[0].plugin, self.plugin.__class__)
        self.assertEqual(ret[0].title, 'Files')
        self.assertEqual(ret[0].value, 1)

    def test_get_category_stats_no_files(self):
        """Test get_category_stats() with no files"""
        self.file.delete()
        ret = self.plugin.get_category_stats(self.category)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0].value, 0)

    def test_get_category_stats_multi_project(self):
        """Test get_category_stats() with files in multiple projects"""
        new_project = self.make_project(
            'NewProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.file = self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=new_project,
            folder=None,
            owner=self.user,
            description='',
            public_url=True,
            secret=build_secret(),
        )
        ret = self.plugin.get_category_stats(self.category)
        self.assertEqual(ret[0].value, 2)  # Both files should be counted

    def test_get_category_stats_multi_category(self):
        """Test get_category_stats() with files in multiple categories"""
        # Create new root category and place new project under it
        new_cat = self.make_project('NewCategory', PROJECT_TYPE_CATEGORY, None)
        new_project = self.make_project(
            'NewProject', PROJECT_TYPE_PROJECT, new_cat
        )
        self.file = self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=self.file_content,
            project=new_project,
            folder=None,
            owner=self.user,
            description='',
            public_url=True,
            secret=build_secret(),
        )
        ret = self.plugin.get_category_stats(self.category)
        self.assertEqual(ret[0].value, 1)  # Only one file should be counted
