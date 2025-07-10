"""Tests for the project settings API in the projectroles app"""

import json

from django.test import override_settings

from test_plus.test import TestCase

from projectroles.app_settings import AppSettingAPI
from projectroles.models import Role, AppSetting, SODAR_CONSTANTS
from projectroles.plugins import PluginAppSettingDef, PluginAPI
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
)


app_settings = AppSettingAPI()
plugin_api = PluginAPI()


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]
APP_SETTING_SCOPE_SITE = SODAR_CONSTANTS['APP_SETTING_SCOPE_SITE']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_TYPE_INTEGER = SODAR_CONSTANTS['APP_SETTING_TYPE_INTEGER']
APP_SETTING_TYPE_JSON = SODAR_CONSTANTS['APP_SETTING_TYPE_JSON']
APP_SETTING_TYPE_STRING = SODAR_CONSTANTS['APP_SETTING_TYPE_STRING']

# Local constants
APP_NAME = 'projectroles'
EXISTING_SETTING = 'project_bool_setting'
EXAMPLE_APP_NAME = 'example_project_app'
INVALID_SETTING_VALUE = 'INVALID VALUE'
INVALID_SETTING_MSG = 'INVALID_SETTING_VALUE detected'
S_PREFIX = 'settings.{}.'


class AppSettingInitMixin:
    """Mixing for initializing app setting data"""

    def init_app_settings(self):
        """Init test app settings"""
        # TODO: Rename these to match the settings in example_project_app
        # TODO: Only create these where it's necessary
        # Init test project settings
        self.project_str_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting',
            'setting_type': APP_SETTING_TYPE_STRING,
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.project_int_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting',
            'setting_type': APP_SETTING_TYPE_INTEGER,
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.project_str_setting_options = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting_options',
            'setting_type': APP_SETTING_TYPE_STRING,
            'value': 'string1',
            'options': ['string1', 'string2'],
            'update_value': 'string2',
            'non_valid_value': 'string3',
        }
        self.project_int_setting_options = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting_options',
            'setting_type': APP_SETTING_TYPE_INTEGER,
            'value': 0,
            'options': [0, 1],
            'update_value': 1,
            'non_valid_value': 2,
        }
        self.project_bool_settings = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_bool_setting',
            'setting_type': APP_SETTING_TYPE_BOOLEAN,
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.project_json_setting = {
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
        # Init test user settings
        self.user_str_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_str_setting',
            'setting_type': APP_SETTING_TYPE_STRING,
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.user_int_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_int_setting',
            'setting_type': APP_SETTING_TYPE_INTEGER,
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.user_str_setting_options = {
            'plugin_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_str_setting_options',
            'setting_type': APP_SETTING_TYPE_STRING,
            'value': 'string1',
            'update_value': 'string2',
            'options': ['string1', 'string2'],
            'non_valid_value': False,
        }
        self.user_int_setting_options = {
            'plugin_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_int_setting_options',
            'setting_type': APP_SETTING_TYPE_INTEGER,
            'value': 0,
            'update_value': 1,
            'options': [0, 1],
            'non_valid_value': 'Nan',
        }
        self.user_bool_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_bool_setting',
            'setting_type': APP_SETTING_TYPE_BOOLEAN,
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.user_json_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'user': self.user,
            'name': 'user_json_setting',
            'setting_type': APP_SETTING_TYPE_JSON,
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }
        # Init test PROJECT_USER settings
        self.project_user_str_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_str_setting',
            'setting_type': APP_SETTING_TYPE_STRING,
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.project_user_int_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_int_setting',
            'setting_type': APP_SETTING_TYPE_INTEGER,
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.project_user_bool_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_bool_setting',
            'setting_type': APP_SETTING_TYPE_BOOLEAN,
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.project_user_json_setting = {
            'plugin_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'user': self.user,
            'name': 'project_user_json_setting',
            'setting_type': APP_SETTING_TYPE_JSON,
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }

        self.settings = [
            self.project_int_setting,
            self.project_int_setting_options,
            self.project_json_setting,
            self.project_str_setting,
            self.project_str_setting_options,
            self.project_bool_settings,
            self.user_int_setting,
            self.user_int_setting_options,
            self.user_json_setting,
            self.user_str_setting,
            self.user_str_setting_options,
            self.user_bool_setting,
            self.project_user_int_setting,
            self.project_user_json_setting,
            self.project_user_str_setting,
            self.project_user_bool_setting,
        ]
        for s in self.settings:
            kwargs = {
                'plugin_name': s['plugin_name'],
                'name': s['name'],
                'setting_type': s['setting_type'],
                'value': (
                    s['value']
                    if s['setting_type'] != APP_SETTING_TYPE_JSON
                    else ''
                ),
                'value_json': (
                    s['value']
                    if s['setting_type'] == APP_SETTING_TYPE_JSON
                    else {}
                ),
            }
            if 'project' in s:
                kwargs['project'] = s['project']
            if 'user' in s:
                kwargs['user'] = s['user']
            self.make_setting(**kwargs)
        return self.settings


class TestAppSettingAPI(
    ProjectMixin,
    RoleAssignmentMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
    AppSettingMixin,
    AppSettingInitMixin,
    TestCase,
):
    """Tests for AppSettingAPI"""

    def setUp(self):
        # Init project
        self.project = self.make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )
        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)
        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self.make_assignment(
            self.project, self.user, self.role_owner
        )
        # Init test data
        self.settings = self.init_app_settings()
        example_plugin = plugin_api.get_app_plugin(EXAMPLE_APP_NAME)
        self.example_defs = example_plugin.app_settings

    def test_get(self):
        """Test get()"""
        for setting in self.settings:
            data = {
                'plugin_name': setting['plugin_name'],
                'setting_name': setting['name'],
            }
            if 'project' in setting:
                data['project'] = setting['project']
            if 'user' in setting:
                data['user'] = setting['user']
            val = app_settings.get(**data)
            self.assertEqual(val, setting['value'])

    def test_get_default(self):
        """Test get() with default value for existing setting"""
        s_defs = app_settings.get_definitions(
            scope=APP_SETTING_SCOPE_PROJECT, plugin_name=EXAMPLE_APP_NAME
        )
        default_val = s_defs[EXISTING_SETTING].default
        val = app_settings.get(
            plugin_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            project=self.project,
        )
        self.assertEqual(val, default_val)

    def test_get_nonexisting(self):
        """Test get() with non-existing setting"""
        with self.assertRaises(KeyError):
            app_settings.get(
                plugin_name=EXAMPLE_APP_NAME,
                setting_name='NON-EXISTING SETTING',
                project=self.project,
            )

    def test_get_post_safe_json(self):
        """Test get() with JSON setting and post_safe=True"""
        val = app_settings.get(
            plugin_name=self.project_json_setting['plugin_name'],
            setting_name=self.project_json_setting['name'],
            project=self.project_json_setting['project'],
            post_safe=True,
        )
        self.assertEqual(type(val), str)

    def test_get_post_safe_str_none(self):
        """Test get() with string setting with null default and post_safe=True"""
        val = app_settings.get(
            plugin_name=self.project_str_setting['plugin_name'],
            setting_name=self.project_str_setting['name'],
            project=self.project_str_setting['project'],
            post_safe=True,
        )
        self.assertEqual(type(val), str)

    def test_get_all_by_scope_project(self):
        """Test get_all_by_scope() with PROJECT scope"""
        all_defs = app_settings.get_all_defs()
        vals = app_settings.get_all_by_scope(
            APP_SETTING_SCOPE_PROJECT, project=self.project
        )
        for k, v in all_defs.items():
            p_vals = [v for v in vals if v.startswith(S_PREFIX.format(k))]
            s_defs = [
                d for d in v.values() if d.scope == APP_SETTING_SCOPE_PROJECT
            ]
            self.assertEqual(len(p_vals), len(s_defs))
            for s_def in s_defs:
                self.assertEqual(
                    vals[f'settings.{k}.{s_def.name}'],
                    app_settings.get(
                        plugin_name=k,
                        setting_name=s_def.name,
                        project=self.project,
                    ),
                )

    def test_get_all_by_scope_user(self):
        """Test get_all_by_scope() with USER scope"""
        all_defs = app_settings.get_all_defs()
        vals = app_settings.get_all_by_scope(
            APP_SETTING_SCOPE_USER, user=self.user
        )
        for k, v in all_defs.items():
            p_vals = [v for v in vals if v.startswith(S_PREFIX.format(k))]
            s_defs = [
                d for d in v.values() if d.scope == APP_SETTING_SCOPE_USER
            ]
            self.assertEqual(len(p_vals), len(s_defs))
            for s_def in s_defs:
                self.assertEqual(
                    vals[f'settings.{k}.{s_def.name}'],
                    app_settings.get(
                        plugin_name=k,
                        setting_name=s_def.name,
                        user=self.user,
                    ),
                )

    def test_get_all_by_scope_project_user(self):
        """Test get_all_by_scope() with PROJECT_USER scope"""
        all_defs = app_settings.get_all_defs()
        vals = app_settings.get_all_by_scope(
            APP_SETTING_SCOPE_PROJECT_USER, project=self.project, user=self.user
        )
        for k, v in all_defs.items():
            p_vals = [v for v in vals if v.startswith(S_PREFIX.format(k))]
            s_defs = [
                d
                for d in v.values()
                if d.scope == APP_SETTING_SCOPE_PROJECT_USER
            ]
            self.assertEqual(len(p_vals), len(s_defs))
            for s_def in s_defs:
                self.assertEqual(
                    vals[f'settings.{k}.{s_def.name}'],
                    app_settings.get(
                        plugin_name=k,
                        setting_name=s_def.name,
                        project=self.project,
                        user=self.user,
                    ),
                )

    def test_get_all_by_scope_site(self):
        """Test get_all_by_scope() with SITE scope"""
        all_defs = app_settings.get_all_defs()
        vals = app_settings.get_all_by_scope(APP_SETTING_SCOPE_SITE)
        for k, v in all_defs.items():
            p_vals = [v for v in vals if v.startswith(S_PREFIX.format(k))]
            s_defs = [
                d for d in v.values() if d.scope == APP_SETTING_SCOPE_SITE
            ]
            self.assertEqual(len(p_vals), len(s_defs))
            for s_def in s_defs:
                self.assertEqual(
                    vals[f'settings.{k}.{s_def.name}'],
                    app_settings.get(
                        plugin_name=k,
                        setting_name=s_def.name,
                    ),
                )

    def test_get_all_by_scope_invalid_args(self):
        """Test get_all_by_scope() with invalid args"""
        with self.assertRaises(ValueError):
            app_settings.get_all_by_scope(
                APP_SETTING_SCOPE_PROJECT_USER, project=self.project  # No user
            )

    def test_is_set_no_object(self):
        """Test is_set() with no setting object set"""
        n = 'project_star'
        kw = {'project': self.project, 'user': self.user}
        self.assertFalse(
            AppSetting.objects.filter(app_plugin=None, name=n, **kw).exists()
        )
        self.assertFalse(
            app_settings.is_set(plugin_name=APP_NAME, setting_name=n, **kw)
        )

    def test_is_set_object_exists(self):
        """Test is_set() with existing setting object"""
        n = 'project_star'
        kw = {'project': self.project, 'user': self.user}
        app_settings.set(plugin_name=APP_NAME, setting_name=n, value=True, **kw)
        self.assertTrue(
            AppSetting.objects.filter(app_plugin=None, name=n, **kw).exists()
        )
        self.assertTrue(
            app_settings.is_set(plugin_name=APP_NAME, setting_name=n, **kw)
        )

    def test_is_set_default_value(self):
        """Test is_set() with existing setting object and default value"""
        n = 'project_star'
        kw = {'project': self.project, 'user': self.user}
        app_settings.set(
            plugin_name=APP_NAME, setting_name=n, value=False, **kw
        )
        self.assertTrue(
            AppSetting.objects.filter(app_plugin=None, name=n, **kw).exists()
        )
        self.assertTrue(
            app_settings.is_set(plugin_name=APP_NAME, setting_name=n, **kw)
        )

    def test_is_set_plugin(self):
        """Test is_set() with plugin setting"""
        n = 'project_str_setting'
        kw = {'project': self.project}
        # NOTE: Already created in setUp()
        self.assertTrue(
            AppSetting.objects.filter(
                app_plugin__name=EXAMPLE_APP_NAME, name=n, **kw
            ).exists()
        )
        self.assertTrue(
            app_settings.is_set(
                plugin_name=EXAMPLE_APP_NAME, setting_name=n, **kw
            )
        )

    def test_is_set_invalid_user(self):
        """Test is_set() with invalid user arg"""
        with self.assertRaises(ValueError):
            app_settings.is_set(
                plugin_name=APP_NAME,
                setting_name='project_star',
                project=self.project,
                user=None,
            )

    def test_set(self):
        """Test set()"""
        for setting in self.settings:
            data = {
                'plugin_name': setting['plugin_name'],
                'setting_name': setting['name'],
            }
            if 'project' in setting:
                data['project'] = setting['project']
            if 'user' in setting:
                data['user'] = setting['user']
            update_data = dict(data)
            update_data['value'] = setting['update_value']

            ret = app_settings.set(**update_data)
            self.assertEqual(ret, True)
            val = app_settings.get(**data)
            self.assertEqual(val, setting['update_value'])

    def test_set_unchanged(self):
        """Test set() with unchanged value"""
        for setting in self.settings:
            data = {
                'plugin_name': setting['plugin_name'],
                'setting_name': setting['name'],
            }
            if 'project' in setting:
                data['project'] = setting['project']
            if 'user' in setting:
                data['user'] = setting['user']

            update_data = dict(data)
            update_data['value'] = setting['value']

            ret = app_settings.set(**update_data)
            self.assertEqual(
                ret,
                False,
                msg='setting={}.{}'.format(
                    setting['plugin_name'], setting['name']
                ),
            )
            val = app_settings.get(**data)
            self.assertEqual(
                val,
                setting['value'],
                msg='setting={}.{}'.format(
                    setting['plugin_name'], setting['name']
                ),
            )

    def test_set_new(self):
        """Test set() with new but defined setting"""
        val = AppSetting.objects.get(
            app_plugin=plugin_api.get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING,
        ).value
        self.assertEqual(bool(int(val)), False)

        ret = app_settings.set(
            plugin_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            value=True,
            project=self.project,
        )
        self.assertEqual(ret, True)
        val = app_settings.get(
            plugin_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            project=self.project,
        )
        self.assertEqual(True, val)
        setting = AppSetting.objects.get(
            app_plugin=plugin_api.get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING,
        )
        self.assertIsInstance(setting, AppSetting)

    def test_set_undefined(self):
        """Test set() with undefined setting (should fail)"""
        with self.assertRaises(ValueError):
            app_settings.set(
                plugin_name=EXAMPLE_APP_NAME,
                setting_name='new_setting',
                value='new',
                project=self.project,
            )

    def test_set_multi_project_user(self):
        """Test set() with multiple instances of PROJECT_USER setting"""
        # Set up second user
        new_user = self.make_user('new_user')
        ret = app_settings.set(
            plugin_name=EXAMPLE_APP_NAME,
            setting_name='project_user_str_setting',
            project=self.project,
            user=self.user,
            value=True,
        )
        self.assertEqual(ret, True)
        ret = app_settings.set(
            plugin_name=EXAMPLE_APP_NAME,
            setting_name='project_user_str_setting',
            project=self.project,
            user=new_user,
            value=True,
        )
        self.assertEqual(ret, True)

    def test_set_invalid_project_types(self):
        """Test set() with invalid project types scope"""
        # Should fail because category_bool_setting has CATEGORY scope
        with self.assertRaises(ValueError):
            app_settings.set(
                plugin_name=EXAMPLE_APP_NAME,
                setting_name='category_bool_setting',
                project=self.project,
                value=True,
            )

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_set_target_local(self):
        """Test setting local setting on target site"""
        n = 'project_str_setting'
        v = 'updated'
        args = {'name': n, 'value': v}
        self.assertEqual(AppSetting.objects.filter(**args).count(), 0)
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        self.assertEqual(AppSetting.objects.filter(**args).count(), 1)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_set_target_local_remote(self):
        """Test setting local setting on target site and remote project"""
        remote_site = self.make_site(
            name='Test source site',
            url='https://sodar.example.com',
            mode=SITE_MODE_SOURCE,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        n = 'project_str_setting'
        v = 'updated'
        args = {'name': n, 'value': v}
        self.assertEqual(AppSetting.objects.filter(**args).count(), 0)
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        self.assertEqual(AppSetting.objects.filter(**args).count(), 1)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_set_target_global(self):
        """Test setting global setting on target site and local project"""
        n = 'project_global_setting'
        self.assertEqual(AppSetting.objects.filter(name=n, value=1).count(), 0)
        app_settings.set(EXAMPLE_APP_NAME, n, True, project=self.project)
        self.assertEqual(AppSetting.objects.filter(name=n, value=1).count(), 1)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_set_target_global_remote(self):
        """Test setting global setting on target site and remote project"""
        remote_site = self.make_site(
            name='Test source site',
            url='https://sodar.example.com',
            mode=SITE_MODE_SOURCE,
        )
        self.make_remote_project(
            project_uuid=self.project.sodar_uuid,
            site=remote_site,
            level=REMOTE_LEVEL_READ_ROLES,
            project=self.project,
        )
        n = 'project_global_setting'
        self.assertEqual(AppSetting.objects.filter(name=n, value=1).count(), 0)
        with self.assertRaises(ValueError):
            app_settings.set(EXAMPLE_APP_NAME, n, True, project=self.project)
        self.assertEqual(AppSetting.objects.filter(name=n, value=1).count(), 0)

    def test_set_user_global(self):
        """Test setting global user setting on source site"""
        n = 'notify_email_project'
        v = '0'
        self.assertEqual(AppSetting.objects.filter(name=n, value=v).count(), 0)
        app_settings.set(APP_NAME, n, False, user=self.user)
        self.assertEqual(AppSetting.objects.filter(name=n, value=v).count(), 1)

    @override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
    def test_set_user_global_target(self):
        """Test setting global user setting on target site"""
        n = 'notify_email_project'
        v = '0'
        self.assertEqual(AppSetting.objects.filter(name=n, value=v).count(), 0)
        with self.assertRaises(ValueError):
            app_settings.set(APP_NAME, n, False, user=self.user)
        self.assertEqual(AppSetting.objects.filter(name=n, value=v).count(), 0)

    def test_validate_boolean(self):
        """Test validate() with type BOOLEAN"""
        for setting in self.settings:
            self.assertEqual(
                app_settings.validate(
                    setting['setting_type'],
                    setting['value'],
                    setting.get('options'),
                ),
                True,
            )
            if setting['setting_type'] == APP_SETTING_TYPE_STRING:
                continue
            with self.assertRaises(ValueError):
                app_settings.validate(
                    setting['setting_type'],
                    setting['non_valid_value'],
                    setting.get('options'),
                )

    def test_validate_int(self):
        """Test validate() with type INTEGER"""
        self.assertEqual(
            app_settings.validate(APP_SETTING_TYPE_INTEGER, 170, None), True
        )
        # NOTE: String is also OK if it corresponds to an int
        self.assertEqual(
            app_settings.validate(APP_SETTING_TYPE_INTEGER, '170', None), True
        )
        with self.assertRaises(ValueError):
            app_settings.validate(
                APP_SETTING_TYPE_INTEGER, 'not an integer', None
            )

    def test_validate_invalid(self):
        """Test validate() with invalid type"""
        with self.assertRaises(ValueError):
            app_settings.validate('INVALID_TYPE', 'value', None)

    def test_get_definition_plugin(self):
        """Test get_definition() with plugin"""
        app_plugin = plugin_api.get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'name': 'project_str_setting',
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': APP_SETTING_TYPE_STRING,
            'label': 'String setting',
            'default': '',
            'description': 'Example string project setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
            'global_edit': False,
            'options': [],
            'project_types': [PROJECT_TYPE_PROJECT],
            'widget_attrs': {},
        }
        s_def = app_settings.get_definition(
            'project_str_setting', plugin=app_plugin
        )
        self.assertIsInstance(s_def, PluginAppSettingDef)
        self.assertEqual(s_def.__dict__, expected)

    def test_get_definition_plugin_name(self):
        """Test get_definition() with plugin name"""
        expected = {
            'name': 'project_str_setting',
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': APP_SETTING_TYPE_STRING,
            'label': 'String setting',
            'default': '',
            'description': 'Example string project setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
            'global_edit': False,
            'options': [],
            'project_types': [PROJECT_TYPE_PROJECT],
            'widget_attrs': {},
        }
        s_def = app_settings.get_definition(
            'project_str_setting', plugin_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(s_def.__dict__, expected)

    def test_get_definition_user(self):
        """Test get_definition() with user setting"""
        expected = {
            'name': 'user_str_setting',
            'scope': APP_SETTING_SCOPE_USER,
            'type': APP_SETTING_TYPE_STRING,
            'label': 'String setting',
            'default': '',
            'description': 'Example string user setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
            'global_edit': False,
            'options': [],
            'project_types': [PROJECT_TYPE_PROJECT],
            'widget_attrs': {},
        }
        s_def = app_settings.get_definition(
            'user_str_setting', plugin_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(s_def.__dict__, expected)

    def test_get_definition_invalid(self):
        """Test get_definition() with innvalid input"""
        with self.assertRaises(ValueError):
            app_settings.get_definition(
                'non_existing_setting', plugin_name=EXAMPLE_APP_NAME
            )
        with self.assertRaises(ValueError):
            app_settings.get_definition(
                'project_str_setting', plugin_name='non_existing_app_name'
            )
        # Both app_name and plugin unset
        with self.assertRaises(ValueError):
            app_settings.get_definition('project_str_setting')

    def test_get_definitions_project(self):
        """Test get_definitions() with PROJECT scope"""
        defs = app_settings.get_definitions(
            APP_SETTING_SCOPE_PROJECT, plugin_name=EXAMPLE_APP_NAME
        )
        self.assertIsInstance(defs, dict)
        ex_defs = [
            d for d in self.example_defs if d.scope == APP_SETTING_SCOPE_PROJECT
        ]
        self.assertEqual(len(defs), len(ex_defs))
        self.assertTrue(
            all([d.scope == APP_SETTING_SCOPE_PROJECT for d in defs.values()])
        )

    def test_get_definitions_user(self):
        """Test get_definitions() with USER scope"""
        defs = app_settings.get_definitions(
            APP_SETTING_SCOPE_USER, plugin_name=EXAMPLE_APP_NAME
        )
        ex_defs = [
            d for d in self.example_defs if d.scope == APP_SETTING_SCOPE_USER
        ]
        self.assertEqual(len(defs), len(ex_defs))
        self.assertTrue(
            all([d.scope == APP_SETTING_SCOPE_USER for d in defs.values()])
        )

    def test_get_definitions_project_user(self):
        """Test get_definitions() with PROJECT_USER scope"""
        defs = app_settings.get_definitions(
            APP_SETTING_SCOPE_PROJECT_USER, plugin_name=EXAMPLE_APP_NAME
        )
        ex_defs = [
            d
            for d in self.example_defs
            if d.scope == APP_SETTING_SCOPE_PROJECT_USER
        ]
        self.assertEqual(len(defs), len(ex_defs))
        self.assertTrue(
            all(
                [
                    d.scope == APP_SETTING_SCOPE_PROJECT_USER
                    for d in defs.values()
                ]
            )
        )

    def test_get_definitions_site(self):
        """Test get_definitions() with SITE scope"""
        defs = app_settings.get_definitions(
            APP_SETTING_SCOPE_SITE, plugin_name=EXAMPLE_APP_NAME
        )
        ex_defs = [
            d for d in self.example_defs if d.scope == APP_SETTING_SCOPE_SITE
        ]
        self.assertEqual(len(defs), len(ex_defs))
        self.assertTrue(list(defs.values())[0].scope, APP_SETTING_SCOPE_SITE)

    def test_get_definitions_no_scope(self):
        """Test get_definitions() with no scope"""
        defs = app_settings.get_definitions(
            scope=None, plugin_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(len(defs), len(self.example_defs))

    def test_get_definitions_modifiable(self):
        """Test get_definitions() with user_modifiable arg"""
        defs = app_settings.get_definitions(
            APP_SETTING_SCOPE_PROJECT, plugin_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(len(defs), 12)
        defs = app_settings.get_definitions(
            APP_SETTING_SCOPE_PROJECT,
            plugin_name=EXAMPLE_APP_NAME,
            user_modifiable=True,
        )
        self.assertEqual(len(defs), 10)

    def test_get_definitions_invalid_scope(self):
        """Test get_definitions() with invalid scope"""
        with self.assertRaises(ValueError):
            app_settings.get_definitions(
                'Ri4thai8aez5ooRa', plugin_name=EXAMPLE_APP_NAME
            )

    def test_get_defaults_project(self):
        """Test get_defaults() with PROJECT scope"""
        prefix = f'settings.{EXAMPLE_APP_NAME}.'
        defaults = app_settings.get_defaults(APP_SETTING_SCOPE_PROJECT)
        self.assertEqual(defaults[prefix + 'project_str_setting'], '')
        self.assertEqual(defaults[prefix + 'project_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'project_bool_setting'], False)
        self.assertEqual(
            defaults[prefix + 'project_json_setting'],
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

    def test_get_defaults_project_post_safe(self):
        """Test get_defaults() with PROJECT scope and post_safe=True"""
        prefix = f'settings.{EXAMPLE_APP_NAME}.'
        defaults = app_settings.get_defaults(
            APP_SETTING_SCOPE_PROJECT, post_safe=True
        )
        self.assertEqual(defaults[prefix + 'project_str_setting'], '')
        self.assertEqual(defaults[prefix + 'project_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'project_bool_setting'], False)
        self.assertEqual(
            defaults[prefix + 'project_json_setting'],
            json.dumps(
                {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False}
            ),
        )

    def test_get_defaults_user(self):
        """Test get_defaults() with USER scope"""
        prefix = f'settings.{EXAMPLE_APP_NAME}.'
        defaults = app_settings.get_defaults(APP_SETTING_SCOPE_USER)
        self.assertEqual(defaults[prefix + 'user_str_setting'], '')
        self.assertEqual(defaults[prefix + 'user_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'user_bool_setting'], False)
        self.assertEqual(
            defaults[prefix + 'user_json_setting'],
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

    def test_get_defaults_project_user(self):
        """Test get_defaults() with PROJECT_USER scope"""
        prefix = f'settings.{EXAMPLE_APP_NAME}.'
        defaults = app_settings.get_defaults(APP_SETTING_SCOPE_PROJECT_USER)
        self.assertEqual(defaults[prefix + 'project_user_str_setting'], '')
        self.assertEqual(defaults[prefix + 'project_user_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'project_user_bool_setting'], False)
        self.assertEqual(
            defaults[prefix + 'project_user_json_setting'],
            {'Example': 'Value', 'list': [1, 2, 3, 4, 5], 'level_6': False},
        )

    def test_get_defaults_site(self):
        """Test get_defaults() with SITE scope"""
        prefix = f'settings.{EXAMPLE_APP_NAME}.'
        defaults = app_settings.get_defaults(APP_SETTING_SCOPE_SITE)
        self.assertEqual(defaults[prefix + 'site_bool_setting'], False)

    def test_delete_scope_project_params_none(self):
        """Test delete() with PROJECT scope and no params (should fail)"""
        self.assertEqual(AppSetting.objects.count(), 16)
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME,
                'project_str_setting',
            )

    def test_delete_scope_project_params_user(self):
        """Test delete() with PROJECT scope and user param"""
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME,
                'project_str_setting',
                user=self.user,
            )

    def test_delete_scope_project_params_project(self):
        """Test delete() with PROJECT scope and project param"""
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete(
            EXAMPLE_APP_NAME,
            'project_str_setting',
            project=self.project,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_scope_project_params_user_project(self):
        """Test delete() with PROJECT scope and user/project params"""
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME,
                'project_str_setting',
                project=self.project,
                user=self.user,
            )

    def test_delete_scope_user_params_none(self):
        """Test delete() with USER scope and no params (should fail)"""
        self.assertEqual(AppSetting.objects.count(), 16)
        with self.assertRaises(ValueError):
            app_settings.delete(EXAMPLE_APP_NAME, 'user_str_setting')

    def test_delete_scope_user_params_user(self):
        """Test delete() with USER scope and user param"""
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete(
            EXAMPLE_APP_NAME, 'user_str_setting', user=self.user
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_scope_user_params_project(self):
        """Test delete() with USER scope and project param"""
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME, 'user_str_setting', project=self.project
            )

    def test_delete_scope_user_params_user_project(self):
        """Test delete() with USER scope and project/user params"""
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME,
                'user_str_setting',
                project=self.project,
                user=self.user,
            )

    def test_delete_scope_project_user_params_none(self):
        """Test delete() with PROJECT_USER scope and no params (should fail)"""
        self.assertEqual(AppSetting.objects.count(), 16)
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME,
                'project_user_str_setting',
                project=None,
                user=None,
            )
        self.assertEqual(AppSetting.objects.count(), 16)

    def test_delete_scope_project_user_params_user(self):
        """Test delete() with PROJECT_USER scope and user param (should fail)"""
        self.assertEqual(AppSetting.objects.count(), 16)
        with self.assertRaises(ValueError):
            app_settings.delete(
                EXAMPLE_APP_NAME,
                'project_user_str_setting',
                project=None,
                user=self.user,
            )
        self.assertEqual(AppSetting.objects.count(), 16)

    def test_delete_scope_project_user_params_project(self):
        """Test delete() with PROJECT_USER scope and project param"""
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete(
            EXAMPLE_APP_NAME,
            'project_user_str_setting',
            project=self.project,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_scope_project_user_params_user_project(self):
        """Test delete() with PROJECT_USER scope and user/project params"""
        self.assertEqual(AppSetting.objects.count(), 16)
        app_settings.delete(
            EXAMPLE_APP_NAME,
            'project_user_str_setting',
            project=self.project,
            user=self.user,
        )
        self.assertEqual(AppSetting.objects.count(), 15)

    def test_delete_by_scope(self):
        """Test delete_by_scope()"""
        self.assertEqual(AppSetting.objects.count(), 16)
        # Delete PROJECT_USER scope settings
        app_settings.delete_by_scope(
            APP_SETTING_SCOPE_PROJECT_USER,
            project=self.project,
            user=self.user,
        )
        self.assertEqual(AppSetting.objects.count(), 12)
        # Delete PROJECT scope settings
        app_settings.delete_by_scope(
            APP_SETTING_SCOPE_USER,
            user=self.user,
        )
        self.assertEqual(AppSetting.objects.count(), 6)
        # Delete USER scope settings
        app_settings.delete_by_scope(
            APP_SETTING_SCOPE_PROJECT,
            project=self.project,
        )
        self.assertEqual(AppSetting.objects.count(), 0)

    def test_delete_by_scope_param_project(self):
        """Test delete_by_scope() with invalid project params"""
        with self.assertRaises(ValueError):
            app_settings.delete_by_scope(
                APP_SETTING_SCOPE_PROJECT,
                project=self.project,
                user=self.user,
            )

    def test_delete_by_scope_param_user(self):
        """Test delete_by_scope() with invalid user params"""
        with self.assertRaises(ValueError):
            app_settings.delete_by_scope(
                APP_SETTING_SCOPE_USER,
                project=self.project,
                user=self.user,
            )

    def test_validate_form_app_settings(self):
        """Test validate_form_app_settings() with valid project setting value"""
        app_plugin = plugin_api.get_app_plugin(EXAMPLE_APP_NAME)
        app_settings = {'project_str_setting': 'String'}
        errors = app_plugin.validate_form_app_settings(
            app_settings, project=self.project
        )
        self.assertEqual(errors, {})

    def test_validate_form_app_settings_invalid(self):
        """Test validate_form_app_settings() with invalid project setting value"""
        app_plugin = plugin_api.get_app_plugin(EXAMPLE_APP_NAME)
        app_settings = {'project_str_setting': INVALID_SETTING_VALUE}
        errors = app_plugin.validate_form_app_settings(
            app_settings, project=self.project
        )
        self.assertEqual(errors, {'project_str_setting': INVALID_SETTING_MSG})

    def test_validate_form_app_settings_user(self):
        """Test validate_form_app_settings() with valid user setting value"""
        app_plugin = plugin_api.get_app_plugin(EXAMPLE_APP_NAME)
        app_settings = {'user_str_setting': 'String'}
        errors = app_plugin.validate_form_app_settings(
            app_settings, user=self.user
        )
        self.assertEqual(errors, {})

    def test_validate_form_app_settings_user_invalid(self):
        """Test validate_form_app_settings() with invalid user setting value"""
        app_plugin = plugin_api.get_app_plugin(EXAMPLE_APP_NAME)
        app_settings = {'user_str_setting': INVALID_SETTING_VALUE}
        errors = app_plugin.validate_form_app_settings(
            app_settings, user=self.user
        )
        self.assertEqual(errors, {'user_str_setting': INVALID_SETTING_MSG})

    def test_compare_value_string(self):
        """Test compare_value() with string values"""
        n = 'project_str_setting'
        v = 'value'
        vf = 'valueXYZ'
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        obj = AppSetting.objects.get(
            app_plugin__name=EXAMPLE_APP_NAME, name=n, project=self.project
        )
        self.assertEqual(app_settings.compare_value(obj, v), True)
        self.assertEqual(app_settings.compare_value(obj, vf), False)

    def test_compare_value_int(self):
        """Test compare_value() with int values"""
        n = 'project_int_setting'
        v = 0
        vf = 1
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        obj = AppSetting.objects.get(
            app_plugin__name=EXAMPLE_APP_NAME, name=n, project=self.project
        )
        self.assertEqual(app_settings.compare_value(obj, v), True)
        self.assertEqual(app_settings.compare_value(obj, vf), False)
        self.assertEqual(app_settings.compare_value(obj, str(v)), True)
        self.assertEqual(app_settings.compare_value(obj, str(vf)), False)

    def test_compare_value_bool(self):
        """Test compare_value() with boolean values"""
        n = 'project_bool_setting'
        v = True
        vf = False
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        obj = AppSetting.objects.get(
            app_plugin__name=EXAMPLE_APP_NAME, name=n, project=self.project
        )
        self.assertEqual(app_settings.compare_value(obj, v), True)
        self.assertEqual(app_settings.compare_value(obj, vf), False)
        self.assertEqual(app_settings.compare_value(obj, '1'), True)
        self.assertEqual(app_settings.compare_value(obj, '0'), False)

    def test_compare_value_json(self):
        """Test compare_value() with JSON values"""
        n = 'project_json_setting'
        v = {'x': 1, 'y': 2}
        vf = {'a': 3, 'b': 4}
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        obj = AppSetting.objects.get(
            app_plugin__name=EXAMPLE_APP_NAME, name=n, project=self.project
        )
        self.assertEqual(app_settings.compare_value(obj, v), True)
        self.assertEqual(app_settings.compare_value(obj, vf), False)

    def test_compare_value_json_empty(self):
        """Test compare_value() with empty JSON values"""
        n = 'project_json_setting'
        v = {}
        vf = {'x': 1, 'y': 2}
        app_settings.set(EXAMPLE_APP_NAME, n, v, project=self.project)
        obj = AppSetting.objects.get(
            app_plugin__name=EXAMPLE_APP_NAME, name=n, project=self.project
        )
        self.assertEqual(app_settings.compare_value(obj, v), True)
        self.assertEqual(app_settings.compare_value(obj, vf), False)
        self.assertEqual(app_settings.compare_value(obj, None), True)
        self.assertEqual(app_settings.compare_value(obj, ''), True)
