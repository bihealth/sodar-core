"""Tests for management commands in the projectroles Django app"""

import os
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from djangoplugins.models import Plugin

from test_plus.test import TestCase

from projectroles.management.commands.batchupdateroles import (
    Command as BatchUpdateRolesCommand,
)
from projectroles.management.commands.cleanappsettings import (
    START_MSG,
    END_MSG,
    DEFINITION_NOT_FOUND_MSG,
    ALLOWED_TYPES_MSG,
    DELETE_PREFIX_MSG,
    DELETE_PROJECT_TYPE_MSG,
    DELETE_SCOPE_MSG,
)
from projectroles.management.commands.createdevusers import DEV_USER_NAMES

from projectroles.models import (
    RoleAssignment,
    ProjectInvite,
    AppSetting,
    SODAR_CONSTANTS,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    AppSettingMixin,
)


User = get_user_model()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
EXAMPLE_APP_NAME = 'example_project_app'
CLEAN_LOG_PREFIX = 'INFO:projectroles.management.commands.cleanappsettings:'


class BatchUpdateRolesMixin:
    """Helpers for batchupdateroles testing"""

    file = None

    def write_file(self, data):
        """Write data to temporary CSV file"""
        if not isinstance(data[0], list):
            data = [data]
        self.file.write(
            bytes('\n'.join([';'.join(r) for r in data]), encoding='utf-8')
        )
        self.file.close()


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


class TestCleanAppSettings(
    ProjectMixin, RoleMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for cleanappsettings command and associated functions"""

    def setUp(self):
        super().setUp()
        # Init roles
        self.init_roles()
        # Init users
        self.user_owner = self.make_user('owner')
        self.user_owner.email = 'owner_user@example.com'
        self.user_owner.save()

        # Init projects
        self.category = self.make_project(
            'top_category', PROJECT_TYPE_CATEGORY, None
        )
        self.cat_owner_as = self.make_assignment(
            self.category, self.user_owner, self.role_owner
        )
        self.project = self.make_project(
            'sub_project', PROJECT_TYPE_PROJECT, self.category
        )
        self.owner_as = self.make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.plugin = Plugin.objects.get(name='example_project_app')

        # Init test setting
        self.setting_str_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting',
            'setting_type': 'STRING',
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.setting_int_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting',
            'setting_type': 'INTEGER',
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.setting_bool_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_bool_setting',
            'setting_type': 'BOOLEAN',
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.setting_json_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_json_setting',
            'setting_type': 'JSON',
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }
        self.setting_iprestrict_values = {
            'app_name': 'projectroles',
            'project': self.project,
            'name': 'ip_restrict',
            'setting_type': 'BOOLEAN',
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
                app_name=s['app_name'],
                name=s['name'],
                setting_type=s['setting_type'],
                value=s['value'] if s['setting_type'] != 'JSON' else '',
                value_json=s['value'] if s['setting_type'] == 'JSON' else {},
                project=s['project'],
            )

    def test_command_undefined(self):
        """Test cleanappsettings with undefined setting"""
        undef_setting = AppSetting(
            app_plugin=self.plugin,
            project=self.project,
            name='ghost',
            type='BOOLEAN',
            value=True,
        )
        undef_setting.save()
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(
            'projectroles.management.commands.cleanappsettings', level='INFO'
        ) as cm:
            call_command('cleanappsettings')
            self.assertEqual(
                cm.output,
                [
                    CLEAN_LOG_PREFIX + START_MSG,
                    (
                        CLEAN_LOG_PREFIX
                        + DELETE_PREFIX_MSG.format(
                            'settings.example_project_app.ghost',
                            self.project.title,
                        )
                        + DEFINITION_NOT_FOUND_MSG
                    ),
                    CLEAN_LOG_PREFIX + END_MSG,
                ],
            )
        self.assertEqual(AppSetting.objects.count(), 5)
        self.assertQuerysetEqual(
            AppSetting.objects.filter(name='ghost'),
            [],
        )

    def test_command_project_types(self):
        """Test cleanappsettings with invalid project types"""
        cat_setting = AppSetting(
            app_plugin=self.plugin,
            project=self.category,
            name='project_user_bool_setting',
            type='BOOLEAN',
            value=True,
        )
        cat_setting.save()
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(
            'projectroles.management.commands.cleanappsettings', level='INFO'
        ) as cm:
            call_command('cleanappsettings')
            self.assertEqual(
                cm.output,
                [
                    CLEAN_LOG_PREFIX + START_MSG,
                    (
                        CLEAN_LOG_PREFIX
                        + DELETE_PREFIX_MSG.format(
                            'settings.example_project_app.'
                            'project_user_bool_setting',
                            self.category.title,
                        )
                        + DELETE_PROJECT_TYPE_MSG.format(
                            self.category.type,
                            ALLOWED_TYPES_MSG,
                            '[\'PROJECT\']',
                        )
                    ),
                    CLEAN_LOG_PREFIX + END_MSG,
                ],
            )
            self.assertEqual(AppSetting.objects.count(), 5)
            self.assertQuerysetEqual(
                AppSetting.objects.filter(name='project_user_bool_setting'),
                [],
            )

    def test_command_project_user_scope(self):
        """Test cleanappsettings with PROJECT_USER scope"""
        user_new = self.make_user('user_new')
        user_new.save()
        pu_setting = AppSetting(
            app_plugin=self.plugin,
            project=self.project,
            user=user_new,
            name='project_user_bool_setting',
            type='BOOLEAN',
            value=True,
        )
        pu_setting.save()
        self.assertEqual(AppSetting.objects.count(), 6)

        with self.assertLogs(
            'projectroles.management.commands.cleanappsettings', level='INFO'
        ) as cm:
            call_command('cleanappsettings')
            self.assertEqual(
                cm.output,
                [
                    CLEAN_LOG_PREFIX + START_MSG,
                    (
                        CLEAN_LOG_PREFIX
                        + DELETE_PREFIX_MSG.format(
                            'settings.example_project_app.'
                            'project_user_bool_setting',
                            self.project.title,
                        )
                        + DELETE_SCOPE_MSG.format(
                            user_new.username,
                        )
                    ),
                    CLEAN_LOG_PREFIX + END_MSG,
                ],
            )
            self.assertEqual(AppSetting.objects.count(), 5)
            self.assertQuerysetEqual(
                AppSetting.objects.filter(name='project_user_bool_setting'),
                [],
            )


@override_settings(DEBUG=True)
class TestCreateDevUsers(TestCase):
    """Tests for createdevusers command"""

    def test_create(self):
        """Test creating users"""
        self.assertEqual(User.objects.count(), 0)
        call_command('createdevusers')
        self.assertEqual(User.objects.count(), len(DEV_USER_NAMES))
        for u in DEV_USER_NAMES:
            user = User.objects.filter(
                username=u,
                name='{} Example'.format(u.capitalize()),
                first_name=u.capitalize(),
                last_name='Example',
                email='{}@example.com'.format(u),
            ).first()
            self.assertIsNotNone(user)

    def test_create_existing(self):
        """Test creating users with existing user in list"""
        self.make_user(DEV_USER_NAMES[0])
        self.assertEqual(User.objects.count(), 1)
        call_command('createdevusers')
        self.assertEqual(User.objects.count(), len(DEV_USER_NAMES))

    def test_create_existing_not_in_list(self):
        """Test creating users with existing user not in list"""
        self.make_user('user_new')
        self.assertEqual(User.objects.count(), 1)
        call_command('createdevusers')
        self.assertEqual(User.objects.count(), len(DEV_USER_NAMES) + 1)

    @override_settings(DEBUG=False)
    def test_create_no_debug(self):
        """Test creating users with debug mode disabled (should fail)"""
        self.assertEqual(User.objects.count(), 0)
        with self.assertRaises(SystemExit):
            call_command('createdevusers')
        self.assertEqual(User.objects.count(), 0)
