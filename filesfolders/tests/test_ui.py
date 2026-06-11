"""UI tests for the filesfolders app"""

from urllib.parse import urlencode

from django.urls import reverse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import AppSetting, SODAR_CONSTANTS
from projectroles.tests.base import ProjectUITestBase
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


class TestProjectFileView(
    FolderMixin, FileMixin, HyperLinkMixin, ProjectUITestBase
):
    """Tests for ProjectFileView UI"""

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
        self.url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
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
        self.assert_element_exists(
            expected_true, self.url, 'sodar-ff-readme-card', True
        )

    def test_ops_dropdown(self):
        """Test operations dropdown visibility"""
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
        self.assert_element_exists(
            expected_true, self.url, 'sodar-ff-file-ops-dropdown', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-ff-file-ops-dropdown', False
        )

    def test_ops_dropdown_archive(self):
        """Test ops dropdown visibility for archived project"""
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
        self.assert_element_exists(
            expected_true, self.url, 'sodar-ff-file-ops-dropdown', True
        )
        self.assert_element_exists(
            expected_false, self.url, 'sodar-ff-file-ops-dropdown', False
        )

    def test_file_dropdown(self):
        """Test file dropdown visibility"""
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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-file-dropdown', 'class'
        )

    def test_file_dropdown_archive(self):
        """Test file dropdown visibility for archived project"""
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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-file-dropdown', 'class'
        )

    def test_folder_dropdown(self):
        """Test folder dropdown visibility"""
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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-folder-dropdown', 'class'
        )

    def test_folder_dropdown_archive(self):
        """Test folder dropdown visibility for archived project"""
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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-folder-dropdown', 'class'
        )

    def test_hyperlink_dropdown(self):
        """Test hyperlink dropdown visibility"""
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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-hyperlink-dropdown', 'class'
        )

    def test_hyperlink_dropdown_archive(self):
        """Test hyperlink dropdown visibility for archived project"""
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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-hyperlink-dropdown', 'class'
        )

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
        self.assert_element_count(expected, self.url, 'sodar-ff-checkbox')

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
        self.assert_element_count(expected, self.url, 'sodar-ff-checkbox')

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
        self.assert_element_count(expected, self.url, 'sodar-ff-link-public')

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
        self.assert_element_count(expected, self.url, 'sodar-ff-link-public')

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
        self.assert_element_count(expected, self.url, 'sodar-ff-link-public')

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
        self.assert_element_count(
            expected, self.url, 'sodar-ff-flag-icon', 'class'
        )


class TestSearch(FolderMixin, FileMixin, HyperLinkMixin, ProjectUITestBase):
    """Tests for the project search UI functionalities"""

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
            flag='FLAG_HEART',
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
        self.url = reverse('projectroles:search')

    def _assert_search_results_count(self, expected, url):
        for expected_user, expected_count in expected:
            self.login_and_redirect(
                expected_user, url, 'sodar-ff-search-table', 'CLASS_NAME'
            )
            elements = self.selenium.find_elements(
                By.CSS_SELECTOR,
                '.sodar-ff-search-table tbody tr',
            )
            self.assertEqual(len(elements), expected_count)

    def _assert_search_results_filtering_count(
        self, filter, before, after, url
    ):
        """
        Utility function to test search result table filtering.

        :param filter: The string to search (str)
        :param before: Expected number of results before filtering (int)
        :param after: Expected number of results after filtering (int)
        :param url: URL with the search query (str)
        """
        self.login_and_redirect(
            self.superuser, url, 'sodar-ff-search-table', 'CLASS_NAME'
        )
        elements = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '.sodar-ff-search-table tbody tr',
        )
        self.assertEqual(len(elements), before)
        f_input = self.selenium.find_element(
            By.XPATH,
            '//div[@data-app-name="filesfolders"]'
            '//input[contains(@class, "sodar-search-filter")]',
        )
        f_input.send_keys(filter)
        if after == 0:
            elements = self.selenium.find_elements(
                By.CSS_SELECTOR,
                '.sodar-ff-search-table tbody tr',
            )
            self.assertEqual(len(elements), 1)
            self.assertEqual(elements[0].text, 'No matching records found')
        else:
            with self.assertRaises(NoSuchElementException):
                self.selenium.find_element(
                    By.CSS_SELECTOR, '.sodar-ff-search-table tbody tr .dt-empty'
                )
            elements = self.selenium.find_elements(
                By.CSS_SELECTOR,
                '.sodar-ff-search-table tbody tr',
            )
            self.assertEqual(len(elements), after)

    def test_search_results_table_layout(self):
        """Test search results table layout"""
        url = self.url + '?' + urlencode({'s': 'descriptio'})
        self.login_and_redirect(
            self.superuser, url, 'sodar-ff-search-table', 'CLASS_NAME'
        )
        thead = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '.sodar-ff-search-table thead th',
        )
        self.assertEqual(len(thead), 5)
        self.assertEqual(
            [th.text for th in thead],
            ['Name', 'Type', 'Project', 'Size', 'Description'],
        )
        tbody_rows = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '.sodar-ff-search-table tbody tr',
        )
        self.assertEqual(len(tbody_rows), 6)

    def test_search_results_highlight(self):
        """Test search results highlight"""
        url = self.url + '?' + urlencode({'s': 'folder_con type:folder'})
        self.login_and_redirect(
            self.superuser, url, 'sodar-ff-search-table', 'CLASS_NAME'
        )
        name_cell = self.selenium.find_element(
            By.CSS_SELECTOR,
            '.sodar-ff-search-table tbody tr td:nth-child(1)',
        )
        name_content = name_cell.find_element(By.TAG_NAME, 'a').get_attribute(
            'innerHTML'
        )
        self.assertEqual(
            name_content,
            '<strong class="sodar-search-highlight">folder_con</strong>tributor',
        )

    def test_search_results_ordering(self):
        """Test search results orderable columns"""
        url = self.url + '?' + urlencode({'s': 'description'})
        self.login_and_redirect(
            self.superuser, url, 'sodar-ff-search-table', 'CLASS_NAME'
        )
        orderable_columns = self.selenium.find_elements(
            By.CSS_SELECTOR,
            '.sodar-ff-search-table .dt-orderable-desc',
        )
        self.assertEqual(
            [col.text for col in orderable_columns],
            ['Name', 'Type', 'Project', 'Size'],
        )

    def test_search_results_filtering(self):
        """Test search results filterable columns"""
        url = self.url + '?' + urlencode({'s': 'description'})
        # Filter on Name column
        self._assert_search_results_filtering_count('contributor', 6, 3, url)
        # Filter on Type column
        self._assert_search_results_filtering_count('hyperlink', 6, 0, url)
        # Filter on Project column
        self._assert_search_results_filtering_count('testproject', 6, 6, url)
        # Filter on Size column
        self._assert_search_results_filtering_count('bytes', 6, 0, url)
        # Filter on Description column
        self._assert_search_results_filtering_count('description', 6, 6, url)
        # Failing filter
        self._assert_search_results_filtering_count('qdrwfu;p', 6, 0, url)

    def test_search_results(self):
        """Test search items visibility according to user permissions"""
        expected = [
            (self.superuser, 6),
            (self.user_owner_cat, 6),
            (self.user_delegate_cat, 6),
            (self.user_contributor_cat, 6),
            (self.user_guest_cat, 6),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 6),
            (self.user_delegate, 6),
            (self.user_contributor, 6),
            (self.user_guest, 6),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'description'})
        self._assert_search_results_count(expected, url)

    def test_search_type_file(self):
        """Test search items visibility with 'file' type"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'file type:file'})
        self._assert_search_results_count(expected, url)

    def test_search_type_folder(self):
        """Test search items visibility with 'folder' type"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'folder type:folder'})
        self._assert_search_results_count(expected, url)

    def test_search_type_link(self):
        """Test search items visibility with 'link' as type"""
        expected = [
            (self.superuser, 2),
            (self.user_owner_cat, 2),
            (self.user_delegate_cat, 2),
            (self.user_contributor_cat, 2),
            (self.user_guest_cat, 2),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 2),
            (self.user_delegate, 2),
            (self.user_contributor, 2),
            (self.user_guest, 2),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'link type:link'})
        self._assert_search_results_count(expected, url)

    def test_search_type_nonexisting(self):
        """Test search items visibility with a nonexisting type"""
        user_types = [
            self.superuser,
            self.user_owner_cat,
            self.user_delegate_cat,
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_viewer_cat,
            self.user_finder_cat,
            self.user_owner,
            self.user_delegate,
            self.user_contributor,
            self.user_guest,
            self.user_viewer,
            self.user_no_roles,
        ]
        url = self.url + '?' + urlencode({'s': 'test type:Jaix1au'})
        for user_type in user_types:
            self.login_and_redirect(user_type, url)
            alert_elem = self.selenium.find_element(
                By.CSS_SELECTOR,
                'div.alert.alert-danger',
            )
            self.assertEqual(
                alert_elem.text, 'Error: Search type "jaix1au" not recognized!'
            )

    def test_search_with_public_link(self):
        """Test public link visibility in search items"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 0),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 0),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'file'})
        self.assert_element_count(
            expected,
            url,
            'Public Link',
            'title',
            wait_elem='sodar-ff-search-table',
            wait_loc='CLASS_NAME',
        )

    def test_search_with_flag(self):
        """Test public link visibility in search items"""
        expected = [
            (self.superuser, 1),
            (self.user_owner_cat, 1),
            (self.user_delegate_cat, 1),
            (self.user_contributor_cat, 1),
            (self.user_guest_cat, 1),
            (self.user_viewer_cat, 0),
            (self.user_finder_cat, 0),
            (self.user_owner, 1),
            (self.user_delegate, 1),
            (self.user_contributor, 1),
            (self.user_guest, 1),
            (self.user_viewer, 0),
            (self.user_no_roles, 0),
        ]
        url = self.url + '?' + urlencode({'s': 'file'})
        self.assert_element_count(
            expected,
            url,
            'sodar-ff-flag-icon',
            'class',
            wait_elem='sodar-ff-search-table',
            wait_loc='CLASS_NAME',
        )


class TestHomeView(ProjectUITestBase):
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
