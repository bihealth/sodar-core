"""UI tests for the filesfolders app"""

from urllib.parse import urlencode

from django.urls import reverse

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import AppSetting, SODAR_CONSTANTS
from projectroles.tests.test_ui import TestUIBase
from projectroles.utils import build_secret

from filesfolders.tests.test_models import (
    FolderMixin,
    FileMixin,
    HyperLinkMixin,
)


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


class TestListView(FolderMixin, FileMixin, HyperLinkMixin, TestUIBase):
    """Tests for filesfolders main file list view UI"""

    def setUp(self):
        super().setUp()
        app_settings.set(
            APP_NAME, 'allow_public_links', True, project=self.project
        )
        self.file_content = bytes('content'.encode('utf-8'))
        self.secret_file_owner = build_secret()
        self.secret_file_contributor = build_secret()
        # Folder created by project owner
        self.folder_owner = self.make_folder(
            name='folder_owner',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        # Folder created by project contributor
        self.folder_contributor = self.make_folder(
            name='folder_contributor',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='',
        )
        # File uploaded by project owner
        self.file_owner = self.make_file(
            name='file_owner.txt',
            file_name='file_owner.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=True,  # NOTE: Public URL OK
            secret=self.secret_file_owner,
        )
        # File uploaded by project contributor
        self.file_contributor = self.make_file(
            name='file_contributor.txt',
            file_name='file_contributor.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='',
            public_url=False,  # NOTE: No public URL
            secret=self.secret_file_contributor,
        )
        # HyperLink added by project owner
        self.hyperlink_owner = self.make_hyperlink(
            name='Owner link',
            url='https://www.bihealth.org/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )
        # HyperLink added by project contributor
        self.hyperlink_contrib = self.make_hyperlink(
            name='Contributor link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='',
        )

    def test_readme(self):
        """Test rendering readme if it has been uploaded to the folder"""
        # Init readme file
        self.readme_file = self.make_file(
            name='readme.txt',
            file_name='readme.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
            public_url=False,
            secret='xxxxxxxxx',
        )
        expected_true = [
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
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-ff-readme-card', True
        )

    def test_buttons_list(self):
        """Test file/folder list-wide button visibility"""
        expected_true = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
        ]
        expected_false = [self.user_guest_cat, self.user_guest]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-ff-buttons-list', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-ff-buttons-list', False
        )

    def test_buttons_list_archive(self):
        """Test file/folder list-wide button visibility for archived project"""
        self.project.set_archive()
        expected_true = [self.superuser]
        expected_false = [
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_exists(
            expected_true, url, 'sodar-ff-buttons-list', True
        )
        self.assert_element_exists(
            expected_false, url, 'sodar-ff-buttons-list', False
        )

    def test_buttons_file(self):
        """Test file action buttons visibility"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 0),  # Does not own files
            (self.user_guest_cat, 0),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-file-buttons')

    def test_buttons_file_archive(self):
        """Test file action buttons visibility for archived project"""
        self.project.set_archive()
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-file-buttons')

    def test_buttons_folder(self):
        """Test folder action buttons visibility"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 0),  # Does not own folders
            (self.user_guest_cat, 0),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-folder-buttons')

    def test_buttons_folder_archive(self):
        """Test folder action buttons visibility for archived project"""
        self.project.set_archive()
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-folder-buttons')

    def test_buttons_hyperlink(self):
        """Test hyperlink action buttons visibility"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 0),  # Does not own hyperlinks
            (self.user_guest_cat, 0),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 1),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-hyperlink-buttons')

    def test_buttons_hyperlink_archive(self):
        """Test hyperlink action buttons visibility for archived project"""
        self.project.set_archive()
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-hyperlink-buttons')

    def test_file_checkboxes(self):
        """Test batch file editing checkbox visibility"""
        expected = [
            (self.superuser, 6),
            (self.user_owner_cat, 6),
            (self.user_delegate_cat, 6),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 6),
            (self.user_delegate, 6),
            (self.user_contributor, 3),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-checkbox')

    def test_file_checkboxes_archive(self):
        """Test batch file editing checkbox visibility for archived project"""
        self.project.set_archive()
        expected = [
            (self.superuser, 6),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-checkbox')

    def test_public_link(self):
        """Test public link visibility"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 0),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-link-public')

    def test_public_link_disable(self):
        """Test public link visibility if allow_public_links is set to False"""
        setting = AppSetting.objects.get(
            project=self.project.pk,
            app_plugin__name=APP_NAME,
            name='allow_public_links',
        )
        setting.value = 0
        setting.save()
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-link-public')

    def test_public_link_archive(self):
        """Test public link visibility for archived project"""
        self.project.set_archive()
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 0),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 0),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-link-public')

    def test_item_flags(self):
        """Test item flagging"""
        # Set up flags
        self.file_owner.flag = 'IMPORTANT'
        self.file_owner.save()
        self.folder_contributor.flag = 'FLAG'
        self.folder_contributor.save()
        self.hyperlink_contrib.flag = 'REVOKED'
        self.hyperlink_contrib.save()
        expected = [
            (self.superuser, 3),
            (self.user_owner_cat, 3),
            (self.user_delegate_cat, 3),
            (self.user_contributor_cat, 3),
            (self.user_guest_cat, 3),
            (self.user_owner, 3),
            (self.user_delegate, 3),
            (self.user_contributor, 3),
            (self.user_guest, 3),
        ]
        url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )
        self.assert_element_count(expected, url, 'sodar-ff-flag-icon', 'class')


class TestSearch(FolderMixin, FileMixin, HyperLinkMixin, TestUIBase):
    """Tests for the project search UI functionalities"""

    def setUp(self):
        super().setUp()
        self.file_content = bytes('content'.encode('utf-8'))
        self.secret_file_owner = build_secret()
        self.secret_file_contributor = build_secret()
        # Folder created by project owner
        self.folder_owner = self.make_folder(
            name='folder_owner',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
        )
        # File created by project contributor
        self.folder_contributor = self.make_folder(
            name='folder_contributor',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='description',
        )
        # File uploaded by project owner
        self.file_owner = self.make_file(
            name='file_owner.txt',
            file_name='file_owner.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
            public_url=True,  # NOTE: Public URL OK
            secret=self.secret_file_owner,
        )
        # File uploaded by project contributor
        self.file_contributor = self.make_file(
            name='file_contributor.txt',
            file_name='file_contributor.txt',
            file_content=self.file_content,
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='description',
            public_url=False,  # NOTE: No public URL
            secret=self.secret_file_contributor,
        )
        # HyperLink added by project owner
        self.hyperlink_owner = self.make_hyperlink(
            name='Owner link',
            url='https://www.bihealth.org/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='description',
        )
        # HyperLink added by project contributor
        self.hyperlink_contrib = self.make_hyperlink(
            name='Contributor link',
            url='http://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_contributor,
            description='description',
        )

    def test_search_results(self):
        """Test search items visibility according to user permissions"""
        expected = [
            (self.superuser, 6),
            (self.user_owner_cat, 6),
            (self.user_delegate_cat, 6),
            (self.user_contributor_cat, 6),
            (self.user_guest_cat, 6),
            (self.user_owner, 6),
            (self.user_delegate, 6),
            (self.user_contributor, 6),
            (self.user_guest, 6),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'description'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_file(self):
        """Test search items visibility with 'file' type"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'file type:file'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_folder(self):
        """Test search items visibility with 'folder' type"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'folder type:folder'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_link(self):
        """Test search items visibility with 'link' as type"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'link type:link'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')

    def test_search_type_nonexisting(self):
        """Test search items visibility with a nonexisting type"""
        expected = [
            (self.superuser, 0),
            (self.user_owner_cat, 0),
            (self.user_delegate_cat, 0),
            (self.user_contributor_cat, 0),
            (self.user_guest_cat, 0),
            (self.user_owner, 0),
            (self.user_delegate, 0),
            (self.user_contributor, 0),
            (self.user_guest, 0),
            (self.user_no_roles, 0),
        ]
        url = (
            reverse('projectroles:search')
            + '?'
            + urlencode({'s': 'test type:Jaix1au'})
        )
        self.assert_element_count(expected, url, 'sodar-ff-search-item')


class TestHomeView(TestUIBase):
    """Tests for appearance of filesfolders specific data in the home view"""

    def test_project_list(self):
        """Test custom filesfolders project list column visibility"""
        users = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
        ]
        url = reverse('home')
        self.assert_element_exists(
            users, url, 'sodar-pr-project-list-header-filesfolders-files', True
        )
        self.assert_element_exists(
            users, url, 'sodar-pr-project-list-header-filesfolders-links', True
        )
