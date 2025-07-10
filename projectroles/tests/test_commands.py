"""Tests for management commands in the projectroles app"""

import os

from tempfile import NamedTemporaryFile
from typing import Union

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.forms.models import model_to_dict
from django.test import override_settings
from djangoplugins.models import Plugin

from test_plus.test import TestCase

# Appalerts dependency
from appalerts.models import AppAlert

# Timeline dependency
from timeline.models import TimelineEvent

from projectroles.app_settings import AppSettingAPI
from projectroles.management.commands.addremotesite import (
    Command as AddRemoteSiteCommand,
)
from projectroles.management.commands.batchupdateroles import (
    Command as BatchUpdateRolesCommand,
)
from projectroles.management.commands.blockprojectaccess import (
    Command as BlockProjectAccessCommand,
    INVALID_PROJECT_TYPE_MSG,
    PROJECT_NOT_FOUND_MSG,
    INVALID_MODE_MSG,
    MODE_CONVERT_ERR_MSG,
)
from projectroles.management.commands.cleanappsettings import (
    LOG_NONE_LABEL,
    START_MSG,
    END_MSG,
    DEF_NOT_FOUND_MSG,
    ALLOWED_TYPES_MSG,
    DELETE_PREFIX_MSG,
    DELETE_PROJECT_TYPE_MSG,
    DELETE_SCOPE_MSG,
)
from projectroles.management.commands.createdevusers import (
    DEV_USER_NAMES,
    DEFAULT_PASSWORD,
)
from projectroles.management.commands.syncgroups import (
    Command as SyncGroupsCommand,
)

from projectroles.models import (
    RoleAssignment,
    ProjectInvite,
    RemoteSite,
    AppSetting,
    SODAR_CONSTANTS,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    AppSettingMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
)
from projectroles.utils import build_secret


app_settings = AppSettingAPI()
User = get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
APP_NAME = 'projectroles'
EXAMPLE_APP_NAME = 'example_project_app'
LOGGER_PREFIX = 'projectroles.management.commands.'
CLEAN_LOG_PREFIX = 'INFO:projectroles.management.commands.cleanappsettings:'
CUSTOM_PASSWORD = 'custompass'
REMOTE_SITE_NAME = 'Test Site'
REMOTE_SITE_URL = 'https://example.com'
REMOTE_SITE_URL2 = 'https://another.site.org'
REMOTE_SITE_SECRET = build_secret(32)
LDAP_DOMAIN = 'EXAMPLE'
INVALID_UUID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'


# Mixins -----------------------------------------------------------------------


class BatchUpdateRolesMixin:
    """
    Helpers for batchupdateroles testing.

    NOTE: May be needed by external repos for testing, do not remove!
    """

    file = None

    def write_file(self, data: Union[str, list]):
        """Write data to temporary CSV file"""
        if not isinstance(data[0], list):
            data = [data]
        self.file.write(
            bytes('\n'.join([';'.join(r) for r in data]), encoding='utf-8')
        )
        self.file.close()


# Tests ------------------------------------------------------------------------


class TestAddRemoteSite(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    TestCase,
):
    """Tests for addremotesite command"""

    def setUp(self):
        self.user = self.make_user('superuser')
        self.user.is_superuser = True
        self.user.save()
        self.command = AddRemoteSiteCommand()
        self.options = {
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SITE_MODE_TARGET,
            'description': '',
            'secret': REMOTE_SITE_SECRET,
            'user_display': True,
            'owner_modifiable': False,
            'suppress_error': False,
        }

    def test_add(self):
        """Test adding new remote site"""
        tl_kwargs = {'event_name': 'target_site_create'}
        self.assertEqual(RemoteSite.objects.count(), 0)
        self.assertEqual(TimelineEvent.objects.filter(**tl_kwargs).count(), 0)
        self.command.handle(**self.options)

        self.assertEqual(RemoteSite.objects.count(), 1)
        site = RemoteSite.objects.first()
        expected = {
            'id': site.pk,
            'name': REMOTE_SITE_NAME,
            'url': REMOTE_SITE_URL,
            'mode': SITE_MODE_TARGET,
            'description': '',
            'secret': REMOTE_SITE_SECRET,
            'sodar_uuid': site.sodar_uuid,
            'user_display': True,
            'owner_modifiable': False,
        }
        self.assertEqual(model_to_dict(site), expected)
        self.assertEqual(TimelineEvent.objects.filter(**tl_kwargs).count(), 1)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_add_source_on_target(self):
        """Test adding source site on target site"""
        tl_kwargs = {'event_name': 'source_site_create'}
        self.options['mode'] = SITE_MODE_SOURCE
        self.assertEqual(RemoteSite.objects.count(), 0)
        self.assertEqual(TimelineEvent.objects.filter(**tl_kwargs).count(), 0)
        self.command.handle(**self.options)
        self.assertEqual(RemoteSite.objects.count(), 1)
        self.assertEqual(TimelineEvent.objects.filter(**tl_kwargs).count(), 1)

    def test_add_source_on_source(self):
        """Test adding source site on source site (should fail)"""
        self.options['mode'] = SITE_MODE_SOURCE
        self.assertEqual(RemoteSite.objects.count(), 0)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 0)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_add_target_on_target(self):
        """Test adding target site on target site (should fail)"""
        self.assertEqual(RemoteSite.objects.count(), 0)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 0)

    def test_add_peer_on_source(self):
        """Test adding peer site on source site (should fail)"""
        self.options['mode'] = SITE_MODE_PEER
        self.assertEqual(RemoteSite.objects.count(), 0)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 0)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_add_peer_on_target(self):
        """Test adding peer site on target site (should fail)"""
        self.options['mode'] = SITE_MODE_PEER
        self.assertEqual(RemoteSite.objects.count(), 0)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 0)

    def test_add_second_target(self):
        """Test adding second target site"""
        self.make_site('Existing Site', REMOTE_SITE_URL2)
        self.assertEqual(RemoteSite.objects.count(), 1)
        self.command.handle(**self.options)
        self.assertEqual(RemoteSite.objects.count(), 2)

    def test_add_second_target_existing_name(self):
        """Test adding second target site with existing name (should fail)"""
        self.make_site(REMOTE_SITE_NAME, REMOTE_SITE_URL2)
        self.assertEqual(RemoteSite.objects.count(), 1)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 1)

    def test_add_second_target_existing_url(self):
        """Test adding second target site with existing URL (should fail)"""
        self.make_site('Existing Site', REMOTE_SITE_URL)
        self.assertEqual(RemoteSite.objects.count(), 1)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 1)

    def test_add_second_target_existing_url_suppress(self):
        """Test adding second target site with suppressed error"""
        self.options['suppress_error'] = True
        self.make_site('Existing Site', REMOTE_SITE_URL)
        self.assertEqual(RemoteSite.objects.count(), 1)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 0)  # No error
        self.assertEqual(RemoteSite.objects.count(), 1)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_add_second_source(self):
        """Test adding second source site (should fail)"""
        self.make_site('Existing Site', REMOTE_SITE_URL2, mode=SITE_MODE_SOURCE)
        self.assertEqual(RemoteSite.objects.count(), 1)
        with self.assertRaises(SystemExit) as cm:
            self.command.handle(**self.options)
        self.assertEqual(cm.exception.code, 1)
        self.assertEqual(RemoteSite.objects.count(), 1)


class TestBatchUpdateRoles(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    BatchUpdateRolesMixin,
    TestCase,
):
    """Tests for batchupdateroles command"""

    def setUp(self):
        super().setUp()
        # Init roles
        self.init_roles()
        # Init users
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()
        self.user_owner_cat = self.make_user('owner_cat')
        self.user_owner_cat.email = 'cat_owner_user@example.com'
        self.user_owner_cat.save()

        # Init projects
        self.category = self.make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Save UUIDs for easy access
        self.category_uuid = str(self.category.sodar_uuid)
        self.project_uuid = str(self.project.sodar_uuid)

        # Init command class
        self.command = BatchUpdateRolesCommand()
        # Init file
        self.file = NamedTemporaryFile(delete=False)

    def tearDown(self):
        if self.file:
            os.remove(self.file.name)
        super().tearDown()

    def test_invite(self):
        """Test inviting a single user via email to project"""
        email = 'new@example.com'
        self.assertEqual(ProjectInvite.objects.count(), 0)

        self.write_file([self.project_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 1)
        invite = ProjectInvite.objects.first()
        self.assertEqual(invite.email, email)
        self.assertEqual(invite.project, self.project)
        self.assertEqual(invite.role, self.role_guest)
        self.assertEqual(invite.issuer, self.user_owner)
        self.assertEqual(len(mail.outbox), 1)

    def test_invite_existing(self):
        """Test inviting a user when they already have an active invite"""
        email = 'new@example.com'
        self.make_invite(email, self.project, self.role_guest, self.user_owner)
        self.assertEqual(ProjectInvite.objects.count(), 1)

        self.write_file([self.project_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_multi_user(self):
        """Test inviting multiple users"""
        email = 'new@example.com'
        email2 = 'new2@example.com'
        self.assertEqual(ProjectInvite.objects.count(), 0)

        fd = [
            [self.project_uuid, email, PROJECT_ROLE_GUEST],
            [self.project_uuid, email2, PROJECT_ROLE_GUEST],
        ]
        self.write_file(fd)
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 2)

    def test_invite_multi_project(self):
        """Test inviting user to multiple projects"""
        email = 'new@example.com'
        self.assertEqual(ProjectInvite.objects.count(), 0)

        fd = [
            [self.category_uuid, email, PROJECT_ROLE_GUEST],
            [self.project_uuid, email, PROJECT_ROLE_GUEST],
        ]
        self.write_file(fd)
        # NOTE: Using user_owner_cat as they have perms for both projects
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner_cat.username}
        )

        self.assertEqual(
            ProjectInvite.objects.filter(project=self.category).count(), 1
        )
        self.assertEqual(
            ProjectInvite.objects.filter(project=self.project).count(), 1
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_invite_owner(self):
        """Test inviting an owner (should fail)"""
        self.write_file(
            [self.project_uuid, 'new@example.com', PROJECT_ROLE_OWNER]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_delegate(self):
        """Test inviting a delegate"""
        self.write_file(
            [self.project_uuid, 'new@example.com', PROJECT_ROLE_DELEGATE]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )
        self.assertEqual(ProjectInvite.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_invite_delegate_no_perms(self):
        """Test inviting a delegate without perms (should fail)"""
        user_delegate = self.make_user('delegate')
        self.make_assignment(self.project, user_delegate, self.role_delegate)
        self.write_file(
            [self.project_uuid, 'new@example.com', PROJECT_ROLE_DELEGATE]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': user_delegate.username}
        )
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_delegate_limit(self):
        """Test inviting a delegate with limit reached (should fail)"""
        user_delegate = self.make_user('delegate')
        self.make_assignment(self.project, user_delegate, self.role_delegate)
        self.write_file(
            [self.project_uuid, 'new@example.com', PROJECT_ROLE_DELEGATE]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add(self):
        """Test adding role to user already in system"""
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        self.assertEqual(ProjectInvite.objects.count(), 0)

        self.write_file([self.project_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as = RoleAssignment.objects.get(
            project=self.project, user=user_new
        )
        self.assertEqual(role_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 1)

    def test_role_update(self):
        """Test updating an existing role for user"""
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        role_as = self.make_assignment(self.project, user_new, self.role_guest)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            1,
        )

        self.write_file([self.project_uuid, email, PROJECT_ROLE_CONTRIBUTOR])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as.refresh_from_db()
        self.assertEqual(role_as.role, self.role_contributor)
        self.assertEqual(len(mail.outbox), 1)

    def test_role_update_owner(self):
        """Test updating the role of current owner (should fail)"""
        email = 'owner@example.com'
        self.user_owner.email = email
        self.user_owner.save()

        self.write_file([self.project_uuid, email, PROJECT_ROLE_CONTRIBUTOR])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.owner_as.refresh_from_db()
        self.assertEqual(self.owner_as.role, self.role_owner)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(PROJECTROLES_DELEGATE_LIMIT=2)
    def test_role_update_delegate_no_perms(self):
        """Test updating a delegate role without perms (should fail)"""
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        role_as = self.make_assignment(self.project, user_new, self.role_guest)
        user_delegate = self.make_user('delegate')
        self.make_assignment(self.project, user_delegate, self.role_delegate)

        self.write_file([self.project_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': user_delegate.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as.refresh_from_db()
        self.assertEqual(role_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 0)

    def test_role_update_delegate_limit(self):
        """Test updating a delegate role with limit reached (should fail)"""
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        role_as = self.make_assignment(self.project, user_new, self.role_guest)
        user_delegate = self.make_user('delegate')
        self.make_assignment(self.project, user_delegate, self.role_delegate)

        self.write_file([self.project_uuid, email, PROJECT_ROLE_DELEGATE])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        role_as.refresh_from_db()
        self.assertEqual(role_as.role, self.role_guest)
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add_inherited_owner(self):
        """Test adding role with inherited owner rank (should fail)"""
        self.write_file(
            [
                self.project_uuid,
                self.user_owner_cat.email,
                PROJECT_ROLE_CONTRIBUTOR,
            ]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=self.user_owner_cat
            ).count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add_inherited_higher(self):
        """Test adding role with inherited role of higher rank"""
        user_new = self.make_user('user_new')
        user_new.email = 'user_new@example.com'
        self.make_assignment(self.category, user_new, self.role_guest)

        self.write_file(
            [
                self.project_uuid,
                user_new.email,
                PROJECT_ROLE_CONTRIBUTOR,
            ]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add_inherited_equal(self):
        """Test adding role with inherited role of equal rank (should fail)"""
        user_new = self.make_user('user_new')
        user_new.email = 'user_new@example.com'
        self.make_assignment(self.category, user_new, self.role_contributor)

        self.write_file(
            [
                self.project_uuid,
                user_new.email,
                PROJECT_ROLE_CONTRIBUTOR,
            ]
        )
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_role_add_inherited_lower(self):
        """Test adding role with inherited role of lower rank (should fail)"""
        user_new = self.make_user('user_new')
        user_new.email = 'user_new@example.com'
        self.make_assignment(self.category, user_new, self.role_contributor)

        self.write_file([self.project_uuid, user_new.email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_invite_and_update(self):
        """Test inviting and updating in one command"""
        email = 'new@example.com'
        user_new = self.make_user('user_new')
        user_new.email = email
        user_new.save()
        email2 = 'new2@example.com'
        self.assertEqual(ProjectInvite.objects.count(), 0)

        fd = [
            [self.project_uuid, email, PROJECT_ROLE_GUEST],
            [self.project_uuid, email2, PROJECT_ROLE_GUEST],
        ]
        self.write_file(fd)
        self.command.handle(
            **{'file': self.file.name, 'issuer': self.user_owner.username}
        )

        self.assertEqual(ProjectInvite.objects.count(), 1)
        self.assertIsNotNone(
            RoleAssignment.objects.filter(
                project=self.project, user=user_new
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_command_no_issuer(self):
        """Test invite without issuer (should go under admin)"""
        admin = self.make_user(settings.PROJECTROLES_DEFAULT_ADMIN)
        admin.is_superuser = True
        admin.save()
        email = 'new@example.com'
        self.write_file([self.project_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(**{'file': self.file.name, 'issuer': None})
        invite = ProjectInvite.objects.first()
        self.assertEqual(invite.issuer, admin)

    def test_command_no_perms(self):
        """Test invite with issuer who lacks permissions for a project"""
        issuer = self.make_user('issuer')
        email = 'new@example.com'
        self.write_file([self.project_uuid, email, PROJECT_ROLE_GUEST])
        self.command.handle(
            **{'file': self.file.name, 'issuer': issuer.username}
        )
        self.assertEqual(ProjectInvite.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)


class TestBlockProjectAccess(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    TestCase,
):
    """Tests for blockprojectaccess command"""

    def _assert_setting(self, value: bool = False):
        """
        Assert project_access_block setting value.

        :param value: Expected value (bool)
        """
        self.assertEqual(
            app_settings.get(
                APP_NAME, 'project_access_block', project=self.project
            ),
            value,
        )

    def setUp(self):
        super().setUp()
        # Init roles
        self.init_roles()
        # Init users
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()
        self.user_owner_cat = self.make_user('owner_cat')
        self.user_owner_cat.email = 'cat_owner_user@example.com'
        self.user_owner_cat.save()
        # Init projects
        self.category = self.make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Save UUIDs for easy access
        self.category_uuid = str(self.category.sodar_uuid)
        self.project_uuid = str(self.project.sodar_uuid)
        # Init command class
        self.command = BlockProjectAccessCommand()
        self.options = {'project': str(self.project.sodar_uuid), 'mode': '1'}
        self.logger_name = LOGGER_PREFIX + 'blockprojectaccess'

    def test_command_set(self):
        """Test blockprojectaccess to set value"""
        self._assert_setting(False)
        self.command.handle(**self.options)
        self._assert_setting(True)

    def test_command_unset(self):
        """Test blockprojectaccess to unset value"""
        app_settings.set(
            APP_NAME, 'project_access_block', True, project=self.project
        )
        self._assert_setting(True)
        self.options['mode'] = '0'
        self.command.handle(**self.options)
        self._assert_setting(False)

    def test_command_same_value(self):
        """Test blockprojectaccess with same value as already set"""
        self._assert_setting(False)
        self.options['mode'] = '0'
        self.command.handle(**self.options)
        self._assert_setting(False)

    def test_command_category(self):
        """Test blockprojectaccess with category (should fail)"""
        self.options['project'] = str(self.category.sodar_uuid)
        with self.assertLogs(self.logger_name, 'ERROR') as cm:
            with self.assertRaises(SystemExit):
                self.command.handle(**self.options)
        self.assertIn(INVALID_PROJECT_TYPE_MSG, cm.output[0])

    def test_command_invalid_uuid(self):
        """Test blockprojectaccess with invalid UUID (should fail)"""
        self.options['project'] = INVALID_UUID
        with self.assertLogs(self.logger_name, 'ERROR') as cm:
            with self.assertRaises(SystemExit):
                self.command.handle(**self.options)
        self.assertIn(
            PROJECT_NOT_FOUND_MSG.format(project_uuid=INVALID_UUID),
            cm.output[0],
        )

    def test_command_value_out_of_range(self):
        """Test blockprojectaccess with value out of range (should fail)"""
        self.options['mode'] = '2'
        with self.assertLogs(self.logger_name, 'ERROR') as cm:
            with self.assertRaises(SystemExit):
                self.command.handle(**self.options)
        self.assertIn(INVALID_MODE_MSG.format(mode='2'), cm.output[0])

    def test_command_value_not_int(self):
        """Test blockprojectaccess with non-integer value (should fail)"""
        self.options['mode'] = 'abc'
        with self.assertLogs(self.logger_name, 'ERROR') as cm:
            with self.assertRaises(SystemExit):
                self.command.handle(**self.options)
        self.assertIn(
            MODE_CONVERT_ERR_MSG.format(mode='abc', ex=TypeError()),
            cm.output[0],
        )


class TestCleanAppSettings(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for cleanappsettings command and associated functions"""

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.save()
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()

        # Init projects
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.plugin = Plugin.objects.get(name='example_project_app')

        # Init test settings
        self.setting_str_values = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting',
            'setting_type': APP_SETTING_TYPE_STRING,
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.setting_int_values = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting',
            'setting_type': APP_SETTING_TYPE_INTEGER,
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.setting_bool_values = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_bool_setting',
            'setting_type': APP_SETTING_TYPE_BOOLEAN,
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.setting_json_values = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_json_setting',
            'setting_type': APP_SETTING_TYPE_JSON,
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }
        self.setting_iprestrict_values = {
            'plugin_name': 'projectroles',
            'project': self.project,
            'name': 'ip_restrict',
            'setting_type': APP_SETTING_TYPE_BOOLEAN,
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.settings = [
            self.setting_int_values,
            self.setting_json_values,
            self.setting_str_values,
            self.setting_bool_values,
            self.setting_iprestrict_values,
        ]
        for s in self.settings:
            self.make_setting(
                plugin_name=s['plugin_name'],
                name=s['name'],
                setting_type=s['setting_type'],
                value=(
                    s['value']
                    if s['setting_type'] != APP_SETTING_TYPE_JSON
                    else ''
                ),
                value_json=(
                    s['value']
                    if s['setting_type'] == APP_SETTING_TYPE_JSON
                    else {}
                ),
                project=s['project'],
            )

        self.cmd_name = 'cleanappsettings'
        self.logger_name = LOGGER_PREFIX + self.cmd_name

    def test_command_undefined_project(self):
        """Test cleanappsettings with undefined PROJECT scope setting"""
        self.make_setting(
            plugin_name=self.plugin.name,
            name='undefined',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
        )
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(self.logger_name, 'INFO') as cm:
            call_command(self.cmd_name)
            self.assertEqual(
                cm.output,
                [
                    CLEAN_LOG_PREFIX + START_MSG,
                    (
                        CLEAN_LOG_PREFIX
                        + DELETE_PREFIX_MSG.format(
                            s_name='settings.example_project_app.undefined',
                            project=f'"{self.project.title}"',
                            user=LOG_NONE_LABEL,
                        )
                        + DEF_NOT_FOUND_MSG
                    ),
                    CLEAN_LOG_PREFIX + END_MSG,
                ],
            )
        self.assertEqual(AppSetting.objects.count(), 5)
        self.assertIsNone(AppSetting.objects.filter(name='undefined').first())

    def test_command_undefined_user(self):
        """Test cleanappsettings with undefined USER scope setting"""
        self.make_setting(
            plugin_name=self.plugin.name,
            name='undefined',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            user=self.user_owner,
        )
        self.assertEqual(AppSetting.objects.count(), 6)
        call_command(self.cmd_name)
        self.assertEqual(AppSetting.objects.count(), 5)

    def test_command_undefined_project_user(self):
        """Test cleanappsettings with undefined PROJECT_USER scope setting"""
        self.make_setting(
            plugin_name=self.plugin.name,
            name='undefined',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=self.user_owner,
        )
        self.assertEqual(AppSetting.objects.count(), 6)
        call_command(self.cmd_name)
        self.assertEqual(AppSetting.objects.count(), 5)

    def test_command_invalid_project_type(self):
        """Test cleanappsettings with invalid project type"""
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.category,
        )
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(self.logger_name, 'INFO') as cm:
            call_command(self.cmd_name)
            self.assertEqual(len(cm.output), 3)
            self.assertEqual(
                cm.output[1],
                (
                    CLEAN_LOG_PREFIX
                    + DELETE_PREFIX_MSG.format(
                        s_name='settings.example_project_app.'
                        'project_user_bool_setting',
                        project=f'"{self.category.title}"',
                        user=LOG_NONE_LABEL,
                    )
                    + DELETE_PROJECT_TYPE_MSG.format(
                        self.category.type, ALLOWED_TYPES_MSG, 'PROJECT'
                    )
                ),
            )
        self.assertEqual(AppSetting.objects.count(), 5)
        self.assertIsNone(
            AppSetting.objects.filter(name='project_user_bool_setting').first()
        )

    def test_command_project_user_scope_no_role(self):
        """Test cleanappsettings with PROJECT_USER scope and no role"""
        user_new = self.make_user('user_new')
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=user_new,
        )
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(self.logger_name, 'INFO') as cm:
            call_command(self.cmd_name)
            self.assertEqual(len(cm.output), 3)
            self.assertEqual(
                cm.output[1],
                (
                    CLEAN_LOG_PREFIX
                    + DELETE_PREFIX_MSG.format(
                        s_name='settings.example_project_app.'
                        'project_user_bool_setting',
                        project=f'"{self.project.title}"',
                        user=f'"{user_new.username}"',
                    )
                    + DELETE_SCOPE_MSG.format(user_new.username)
                ),
            )
        self.assertEqual(AppSetting.objects.count(), 5)
        self.assertIsNone(
            AppSetting.objects.filter(name='project_user_bool_setting').first()
        )

    def test_command_project_user_scope_role(self):
        """Test cleanappsettings with PROJECT_USER scope and existing role"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.project, user_new, self.role_contributor)
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=user_new,
        )
        self.assertEqual(AppSetting.objects.count(), 6)
        call_command(self.cmd_name)
        self.assertEqual(AppSetting.objects.count(), 6)

    def test_command_project_user_superuser(self):
        """Test PROJECT_USER scope with no role as superuser"""
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=self.superuser,
        )
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(self.logger_name, 'INFO') as cm:
            call_command(self.cmd_name)
            self.assertEqual(len(cm.output), 2)
        self.assertEqual(AppSetting.objects.count(), 6)
        self.assertIsNotNone(
            AppSetting.objects.filter(name='project_user_bool_setting').first()
        )

    def test_command_project_user_superuser_enable(self):
        """Test PROJECT_USER scope with no role as superuser with deletion enabled"""
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=self.superuser,
        )
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(self.logger_name, 'INFO') as cm:
            call_command(self.cmd_name, superuser=True)
            self.assertEqual(len(cm.output), 3)
            self.assertEqual(
                cm.output[1],
                (
                    CLEAN_LOG_PREFIX
                    + DELETE_PREFIX_MSG.format(
                        s_name='settings.example_project_app.'
                        'project_user_bool_setting',
                        project=f'"{self.project.title}"',
                        user=f'"{self.superuser.username}"',
                    )
                    + DELETE_SCOPE_MSG.format(self.superuser.username)
                ),
            )
        self.assertEqual(AppSetting.objects.count(), 5)
        self.assertIsNone(
            AppSetting.objects.filter(name='project_user_bool_setting').first()
        )

    def test_command_check(self):
        """Test cleanappsettings with check mode enabled"""
        user_new = self.make_user('user_new')
        self.make_setting(
            plugin_name=self.plugin.name,
            name='undefined',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
        )
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.category,
        )
        self.make_setting(
            plugin_name=self.plugin.name,
            name='project_user_bool_setting',
            setting_type=APP_SETTING_TYPE_BOOLEAN,
            value=True,
            project=self.project,
            user=user_new,
        )
        self.assertEqual(AppSetting.objects.count(), 8)

        with self.assertLogs(self.logger_name, 'INFO') as cm:
            call_command(self.cmd_name, check=True)
            self.assertEqual(len(cm.output), 6)
        self.assertEqual(AppSetting.objects.count(), 8)


class TestRemoveRoles(
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    TestCase,
):
    """Tests for removeroles command"""

    def setUp(self):
        # Init roles
        self.init_roles()
        # Init users
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_owner = self.make_user('user_owner')
        self.user = self.make_user('user')
        # Init projects
        self.category = self.make_project(
            'TestCategory', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.project = self.make_project(
            'TestProject', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        # Set other variables
        self.cmd_name = 'removeroles'

    def test_command(self):
        """Test removing non-owner roles from user"""
        # Set up non-owner roles for user in category and project
        self.make_assignment(self.category, self.user, self.role_contributor)
        self.make_assignment(self.project, self.user, self.role_guest)
        # Set up another user to ensure we keep their roles
        user_keep = self.make_user('user_keep')
        self.make_assignment(self.category, user_keep, self.role_contributor)
        self.make_assignment(self.project, user_keep, self.role_guest)

        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(self.category.has_role(user_keep), True)
        self.assertEqual(self.project.has_role(user_keep), True)
        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.assertEqual(self.user.is_active, True)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='role_delete').count(), 0
        )
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_delete').count(), 0
        )

        call_command(self.cmd_name, user=self.user)
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(self.category.has_role(user_keep), True)
        self.assertEqual(self.project.has_role(user_keep), True)
        self.assertEqual(self.category.has_role(self.user), False)
        self.assertEqual(self.project.has_role(self.user), False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, True)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='role_delete').count(), 2
        )
        # App alerts should not be created
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_delete').count(), 0
        )

    def test_command_deactivate(self):
        """Test removing roles from user with deactivation"""
        # Set up non-owner roles for user in category and project
        self.make_assignment(self.category, self.user, self.role_contributor)
        self.make_assignment(self.project, self.user, self.role_guest)
        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.assertEqual(self.user.is_active, True)
        call_command(self.cmd_name, user=self.user, deactivate=True)
        self.assertEqual(self.category.has_role(self.user), False)
        self.assertEqual(self.project.has_role(self.user), False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, False)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_command_remote(self):
        """Test removing roles from remote project"""
        self.make_assignment(self.category, self.user, self.role_contributor)
        self.make_assignment(self.project, self.user, self.role_guest)
        remote_site = self.make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SITE_MODE_SOURCE,
        )
        self.make_remote_project(
            project_uuid=self.category.sodar_uuid,
            site=remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.category,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )

        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.assertEqual(self.category.is_remote(), True)
        self.assertEqual(self.project.is_remote(), True)

        call_command(self.cmd_name, user=self.user)
        # Roles should not be removed
        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)

    def test_command_check(self):
        """Test command with check mode and non-owner role"""
        self.make_assignment(self.category, self.user, self.role_contributor)
        self.make_assignment(self.project, self.user, self.role_guest)

        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='role_delete').count(), 0
        )
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_delete').count(), 0
        )

        call_command(self.cmd_name, user=self.user, check=True)
        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.assertEqual(
            TimelineEvent.objects.filter(event_name='role_delete').count(), 0
        )
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_delete').count(), 0
        )

    def test_command_check_deactivate(self):
        """Test command with check mode and deactivation"""
        self.make_assignment(self.category, self.user, self.role_contributor)
        self.make_assignment(self.project, self.user, self.role_guest)
        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.assertEqual(self.user.is_active, True)
        call_command(self.cmd_name, user=self.user, check=True, deactivate=True)
        self.assertEqual(self.category.has_role(self.user), True)
        self.assertEqual(self.project.has_role(self.user), True)
        self.user.refresh_from_db()
        self.assertEqual(self.user.is_active, True)

    def test_command_owner_unset(self):
        """Test removing owner with unset new owner"""
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        # Inherited owner role
        self.assertEqual(self.project.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(
            TimelineEvent.objects.filter(
                event_name='role_owner_transfer'
            ).count(),
            0,
        )
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_update').count(), 0
        )

        call_command(self.cmd_name, user=self.user_owner)
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), False)
        # Assert local owner roles
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)
        self.assertEqual(self.project.get_owner().user, self.user_owner_cat)
        self.assertEqual(
            TimelineEvent.objects.filter(
                event_name='role_owner_transfer'
            ).count(),
            1,
        )
        # No alerts for inherited owner or old removed user
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_update').count(), 0
        )

    def test_command_owner_unset_top_level(self):
        """Test removing owner with unset new owner at top level (should fail)"""
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        call_command(self.cmd_name, user=self.user_owner_cat)
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)

    def test_command_owner_unset_same_owner(self):
        """Test removing owner with unset new owner and same owner on all levels (should fail)"""
        self.owner_as.user = self.user_owner_cat
        self.owner_as.save()
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)
        self.assertEqual(self.project.get_owner().user, self.user_owner_cat)
        call_command(self.cmd_name, user=self.user_owner_cat)
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)
        self.assertEqual(self.project.get_owner().user, self.user_owner_cat)

    def test_command_owner_set_no_role(self):
        """Test removing owner role with set new owner without existing role"""
        user_new = self.make_user('user_new')
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(self.project.has_role(user_new), False)
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_update').count(), 0
        )
        call_command(self.cmd_name, user=self.user_owner, owner=user_new)
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), False)
        self.assertEqual(self.project.get_owner().user, user_new)
        # Alert for new owner
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_update').count(), 1
        )

    def test_command_owner_set_no_role_top_level(self):
        """Test removing owner role with set new owner without existing role on top level"""
        user_new = self.make_user('user_new')
        self.assertEqual(self.category.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner_cat), True)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(self.project.has_role(user_new), False)
        call_command(self.cmd_name, user=self.user_owner_cat, owner=user_new)
        self.assertEqual(self.category.has_role(self.user_owner_cat), False)
        self.assertEqual(self.project.has_role(self.user_owner_cat), False)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(self.category.get_owner().user, user_new)
        self.assertEqual(self.project.has_role(user_new), True)

    def test_command_owner_set_existing_role(self):
        """Test removing owner role with set new owner and existing role"""
        user_new = self.make_user('user_new')
        self.make_assignment(self.project, user_new, self.role_contributor)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        self.assertEqual(self.project.has_role(user_new), True)
        self.assertEqual(
            RoleAssignment.objects.filter(user=user_new).count(), 1
        )
        call_command(self.cmd_name, user=self.user_owner, owner=user_new)
        self.assertEqual(self.project.get_owner().user, user_new)
        self.assertEqual(self.project.has_role(self.user_owner), False)
        self.assertEqual(
            RoleAssignment.objects.filter(user=user_new).count(), 1
        )

    def test_command_owner_invalid_new_owner_name(self):
        """Test removing owner with invalid new owner name (should fail)"""
        self.assertEqual(self.project.has_role(self.user_owner), True)
        with self.assertRaises(SystemExit):
            call_command(
                self.cmd_name, user=self.user_owner, owner='INVALID-NAME'
            )
        self.assertEqual(self.project.has_role(self.user_owner), True)

    def test_command_owner_check(self):
        """Test command with check mode and owner role"""
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(
            TimelineEvent.objects.filter(
                event_name='role_owner_transfer'
            ).count(),
            0,
        )
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_update').count(), 0
        )

        call_command(self.cmd_name, user=self.user_owner, check=True)
        self.assertEqual(self.project.has_role(self.user_owner), True)
        self.assertEqual(self.category.get_owner().user, self.user_owner_cat)
        self.assertEqual(self.project.get_owner().user, self.user_owner)
        self.assertEqual(
            TimelineEvent.objects.filter(
                event_name='role_owner_transfer'
            ).count(),
            0,
        )
        self.assertEqual(
            AppAlert.objects.filter(alert_name='role_update').count(), 0
        )


class TestSyncGroups(TestCase):
    """Tests for syncgroups command"""

    def setUp(self):
        self.command = SyncGroupsCommand()

    def test_sync_system(self):
        """Test sync with system username"""
        user = self.make_user('user')
        user.groups.all().delete()  # Remove groups
        self.assertEqual(user.groups.count(), 0)
        self.command.handle()
        self.assertEqual(user.groups.count(), 1)
        group = user.groups.first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, SYSTEM_USER_GROUP)

    def test_sync_system_existing(self):
        """Test sync with system username and existing group"""
        user = self.make_user('user')
        self.assertEqual(user.groups.count(), 1)
        self.command.handle()
        self.assertEqual(user.groups.count(), 1)
        group = user.groups.first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, SYSTEM_USER_GROUP)

    @override_settings(AUTH_LDAP_USERNAME_DOMAIN=LDAP_DOMAIN)
    def test_sync_ldap(self):
        """Test sync with LDAP user"""
        user = self.make_user('user@' + LDAP_DOMAIN)
        user.groups.all().delete()
        self.assertEqual(user.groups.count(), 0)
        self.command.handle()
        self.assertEqual(user.groups.count(), 1)
        group = user.groups.first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, LDAP_DOMAIN.lower())

    @override_settings(AUTH_LDAP_USERNAME_DOMAIN=LDAP_DOMAIN)
    def test_sync_ldap_existing(self):
        """Test sync with LDAP user and existing group"""
        user = self.make_user('user@' + LDAP_DOMAIN)
        self.assertEqual(user.groups.count(), 1)
        self.command.handle()
        self.assertEqual(user.groups.count(), 1)
        group = user.groups.first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, LDAP_DOMAIN.lower())


@override_settings(DEBUG=True)
class TestCreateDevUsers(TestCase):
    """Tests for createdevusers command"""

    def setUp(self):
        super().setUp()
        self.cmd_name = 'createdevusers'

    def test_create(self):
        """Test creating users"""
        self.assertEqual(User.objects.count(), 0)
        call_command(self.cmd_name)
        self.assertEqual(User.objects.count(), len(DEV_USER_NAMES))
        for u in DEV_USER_NAMES:
            user = User.objects.filter(
                username=u,
                name=f'{u.capitalize()} Example',
                first_name=u.capitalize(),
                last_name='Example',
                email=f'{u}@example.com',
            ).first()
            self.assertIsNotNone(user)
            self.assertEqual(user.check_password(DEFAULT_PASSWORD), True)

    def test_create_custom_password(self):
        """Test creating users with custom password"""
        call_command(self.cmd_name, password=CUSTOM_PASSWORD)
        for u in DEV_USER_NAMES:
            user = User.objects.filter(username=u).first()
            self.assertEqual(user.check_password(CUSTOM_PASSWORD), True)

    def test_create_existing(self):
        """Test creating users with existing user in list"""
        self.make_user(DEV_USER_NAMES[0])
        self.assertEqual(User.objects.count(), 1)
        call_command(self.cmd_name)
        self.assertEqual(User.objects.count(), len(DEV_USER_NAMES))

    def test_create_existing_not_in_list(self):
        """Test creating users with existing user not in list"""
        self.make_user('user_new')
        self.assertEqual(User.objects.count(), 1)
        call_command(self.cmd_name)
        self.assertEqual(User.objects.count(), len(DEV_USER_NAMES) + 1)

    @override_settings(DEBUG=False)
    def test_create_no_debug(self):
        """Test creating users with debug mode disabled (should fail)"""
        self.assertEqual(User.objects.count(), 0)
        with self.assertRaises(SystemExit):
            call_command(self.cmd_name)
        self.assertEqual(User.objects.count(), 0)
