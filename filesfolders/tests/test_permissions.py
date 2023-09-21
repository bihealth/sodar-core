"""Tests for UI view permissions in the filesfolders app"""

from django.test import override_settings
from django.urls import reverse

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_permissions import TestProjectPermissionBase

from filesfolders.tests.test_models import (
    FileMixin,
    FolderMixin,
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
SECRET = '7dqq83clo2iyhg29hifbor56og6911r5'


# Base Classes and Mixins ------------------------------------------------------


class FilesfoldersPermissionTestMixin(FolderMixin, FileMixin, HyperLinkMixin):
    """Mixin for filesfolders view permission test helpers"""

    def make_test_folder(self):
        return self.make_folder(
            name='folder',
            project=self.project,
            folder=None,
            owner=self.user_owner,  # Project owner is the owner of folder
            description='',
        )

    def make_test_file(self, public=False):
        if public:
            app_settings.set(
                APP_NAME, 'allow_public_links', True, project=self.project
            )
        return self.make_file(
            name='file.txt',
            file_name='file.txt',
            file_content=bytes('content'.encode('utf-8')),
            project=self.project,
            folder=None,
            owner=self.user_owner,  # Project owner is the file owner
            description='',
            public_url=public,
            secret=SECRET,
        )

    def make_test_link(self):
        return self.make_hyperlink(
            name='Link',
            url='https://www.google.com/',
            project=self.project,
            folder=None,
            owner=self.user_owner,
            description='',
        )


# Test Cases -------------------------------------------------------------------


class TestProjectFileViewPermissions(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for ProjectFileView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:list', kwargs={'project': self.project.sodar_uuid}
        )

    def test_get(self):
        """Test ProjectFileView GET"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        # Test public project
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 200)

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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)


class TestFolderCreateView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FolderCreateView view permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:folder_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test FolderCreateView GET"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    def test_get_category(self):
        """Test GET with folder under category (should fail)"""
        url = reverse(
            'filesfolders:folder_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        bad_users = [
            self.superuser,
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
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)


class TestFolderUpdateView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FolderUpdateView permissions"""

    def setUp(self):
        super().setUp()
        folder = self.make_test_folder()
        self.url = reverse(
            'filesfolders:folder_update',
            kwargs={'item': folder.sodar_uuid},
        )

    def test_get(self):
        """Test FolderUpdateView GET"""
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
            self.user_contributor,  # NOTE: not the owner of the folder
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestFolderDeleteView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FolderDeleteView permissions"""

    def setUp(self):
        super().setUp()
        folder = self.make_test_folder()
        self.url = reverse(
            'filesfolders:folder_delete',
            kwargs={'item': folder.sodar_uuid},
        )

    def test_get(self):
        """Test FolderDeleteView GET"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestFileCreateView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests FileCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:file_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test FileCreateView GET"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    def test_get_category(self):
        """Test GET under category (should fail)"""
        url = reverse(
            'filesfolders:file_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        bad_users = [
            self.superuser,
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
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)


class TestFileUpdateView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FileUpdateView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file()
        self.url = reverse(
            'filesfolders:file_update', kwargs={'item': file.sodar_uuid}
        )

    def test_get(self):
        """Test FileUpdateView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
            self.user_delegate_cat,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_contributor,  # NOTE: not the owner of the file
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestFileDeleteView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FileDeleteView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file()
        self.url = reverse(
            'filesfolders:file_delete', kwargs={'item': file.sodar_uuid}
        )

    def test_get(self):
        """Test FileDeleteView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
            self.user_delegate_cat,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestFilePublicLinkView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FilePublicLinkView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file(public=True)
        self.url = reverse(
            'filesfolders:file_public_link',
            kwargs={'file': file.sodar_uuid},
        )

    def test_get(self):
        """Test FilePublicLinkView GET"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test get with archived project"""
        self.project.set_archive()
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestFileServeView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FileServeView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file()
        self.url = reverse(
            'filesfolders:file_serve',
            kwargs={'file': file.sodar_uuid, 'file_name': file.name},
        )

    def test_get(self):
        """Test FileServeView GET"""
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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 200)

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
        bad_users = [self.user_finder_cat, self.user_no_roles, self.anonymous]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, self.user_no_roles, 200)
        self.assert_response(self.url, self.anonymous, 302)


class TestFileServePublicView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for FileServePublicView permissions"""

    def setUp(self):
        super().setUp()
        file = self.make_test_file(public=True)
        self.url = reverse(
            'filesfolders:file_serve_public',
            kwargs={'secret': SECRET, 'file_name': file.name},
        )

    def test_get(self):
        """Test FileServePublicView GET"""
        good_users = [
            self.superuser,
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 200
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 200)

    def test_get_archived(self):
        """Test FileServePublicView GET with archived project"""
        self.project.set_archive()
        good_users = [
            self.superuser,
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.project.set_public()
        self.assert_response(
            self.url, [self.user_no_roles, self.anonymous], 200
        )

    def test_get_disabled(self):
        """Test GET with public links disabled (should fail)"""
        app_settings.set(
            APP_NAME, 'allow_public_links', False, project=self.project
        )
        bad_users = [
            self.superuser,
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
            self.anonymous,
        ]
        self.assert_response(self.url, bad_users, 400)


class TestHyperLinkCreateView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for HyperLinkCreateView permissions"""

    def setUp(self):
        super().setUp()
        self.url = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'project': self.project.sodar_uuid},
        )

    def test_get(self):
        """Test HyperLinkCreateView GET"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    def test_get_category(self):
        """Test GET under category (should fail)"""
        url = reverse(
            'filesfolders:hyperlink_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        bad_users = [
            self.superuser,
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
            self.anonymous,
        ]
        self.assert_response(url, bad_users, 302)


class TestHyperLinkUpdateView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for HyperLinkUpdateView permissions"""

    def setUp(self):
        super().setUp()
        link = self.make_test_link()
        self.url = reverse(
            'filesfolders:hyperlink_update',
            kwargs={'item': link.sodar_uuid},
        )

    def test_get(self):
        """Test HyperLinkUpdateView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
            self.user_delegate_cat,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_contributor,
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test hyperlink updating with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestHyperLinkDeleteView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for HyperLinkDeleteView permissions"""

    def setUp(self):
        super().setUp()
        link = self.make_test_link()
        self.url = reverse(
            'filesfolders:hyperlink_update',
            kwargs={'item': link.sodar_uuid},
        )

    def test_get(self):
        """Test HyperLinkDeleteView GET"""
        good_users = [
            self.superuser,
            self.user_owner_cat,
            self.user_owner,
            self.user_delegate_cat,
            self.user_delegate,
        ]
        bad_users = [
            self.user_contributor_cat,
            self.user_guest_cat,
            self.user_finder_cat,
            self.user_contributor,  # NOTE: not the owner of the link
            self.user_guest,
            self.user_no_roles,
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_get_anon(self):
        """Test GET with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

    def test_get_archive(self):
        """Test GET with archived project"""
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
            self.anonymous,
        ]
        self.assert_response(self.url, good_users, 200)
        self.assert_response(self.url, bad_users, 302)
        self.project.set_public()
        self.assert_response(self.url, bad_users, 302)


class TestBatchEditView(
    FilesfoldersPermissionTestMixin, TestProjectPermissionBase
):
    """Tests for BatchEditView permissions"""

    def setUp(self):
        super().setUp()
        folder = self.make_test_folder()
        self.url = reverse(
            'filesfolders:batch_edit',
            kwargs={'project': self.project.sodar_uuid},
        )
        self.post_data = {
            'batch-action': 'delete',
            'user-confirmed': '0',
            'batch_item_Folder_{}'.format(folder.sodar_uuid): '1',
        }

    def test_post(self):
        """Test BatchEditView POST"""
        # NOTE: Contributor is OK as checks for object perms happen after POST
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
        self.assert_response(
            self.url, good_users, 200, method='POST', data=self.post_data
        )
        self.assert_response(
            self.url, bad_users, 302, method='POST', data=self.post_data
        )
        self.project.set_public()
        self.assert_response(
            self.url, bad_users, 302, method='POST', data=self.post_data
        )

    @override_settings(PROJECTROLES_ALLOW_ANONYMOUS=True)
    def test_post_anon(self):
        """Test POST with anonymous access"""
        self.project.set_public()
        self.assert_response(self.url, self.anonymous, 302)

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
        self.assert_response(
            self.url, good_users, 200, method='POST', data=self.post_data
        )
        self.assert_response(
            self.url, bad_users, 302, method='POST', data=self.post_data
        )
        self.project.set_public()
        self.assert_response(
            self.url, bad_users, 302, method='POST', data=self.post_data
        )
