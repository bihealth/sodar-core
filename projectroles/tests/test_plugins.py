"""Tests for plugins in the projectroles Django app"""

from test_plus.test import TestCase

from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import PluginAppSettingDef

# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
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
DEF_SCOPE_INVALID = 'INVALID_SCOPE'
DEF_TYPE_INVALID = 'INVALID_TYPE'
DEF_NAME = 'test_app_setting'
DEF_LABEL = 'Label'
DEF_PLACEHOLDER = 'placeholder'
DEF_DESC = 'description'
DEF_WIDGET_ATTRS = {'class': 'text-danger'}
DEF_JSON_VALUE = {
    'Example': 'Value',
    'list': [1, 2, 3, 4, 5],
    'level_6': False,
}


class TestPluginAppSettingDef(TestCase):
    """Tests for PluginAppSettingDef"""

    def test_init(self):
        """Test PluginAppSettingDef initialization"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_STRING,
        )
        expected = {
            'name': DEF_NAME,
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': APP_SETTING_TYPE_STRING,
            'default': None,
            'label': None,
            'placeholder': None,
            'description': None,
            'options': [],
            'user_modifiable': True,
            'global_edit': False,
            'project_types': [PROJECT_TYPE_PROJECT],
            'widget_attrs': {},
        }
        self.assertEqual(s_def.__dict__, expected)

    def test_init_no_defaults(self):
        """Test init with no default values"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_STRING,
            default='string',
            label=DEF_LABEL,
            placeholder=DEF_PLACEHOLDER,
            description=DEF_DESC,
            options=['string', 'string2'],
            user_modifiable=False,
            global_edit=True,
            project_types=[PROJECT_TYPE_PROJECT, PROJECT_TYPE_CATEGORY],
            widget_attrs=DEF_WIDGET_ATTRS,
        )
        expected = {
            'name': DEF_NAME,
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': APP_SETTING_TYPE_STRING,
            'default': 'string',
            'label': DEF_LABEL,
            'placeholder': DEF_PLACEHOLDER,
            'description': DEF_DESC,
            'options': ['string', 'string2'],
            'user_modifiable': False,
            'global_edit': True,
            'project_types': [PROJECT_TYPE_PROJECT, PROJECT_TYPE_CATEGORY],
            'widget_attrs': DEF_WIDGET_ATTRS,
        }
        self.assertEqual(s_def.__dict__, expected)

    def test_init_option_default_tuple(self):
        """Test init with option label tuples and default value"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_STRING,
            default='string2',
            options=['string', ('string2', 'string2 label')],
        )
        self.assertIsNotNone(s_def)

    def test_init_invalid_scope(self):
        """Test init with invalid scope"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=DEF_SCOPE_INVALID,
                type=APP_SETTING_TYPE_STRING,
            )

    def test_init_invalid_type(self):
        """Test init with invalid type"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT,
                type=DEF_TYPE_INVALID,
            )

    def test_init_invalid_option_type(self):
        """Test init with invalid option type"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT,
                type=APP_SETTING_TYPE_BOOLEAN,
                options=['string', 'string2'],
            )

    def test_init_default_boolean(self):
        """Test init with BOOLEAN type and valid default"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_BOOLEAN,
            default=True,
        )
        self.assertIsNotNone(s_def)

    def test_init_default_boolean_invalid(self):
        """Test init with BOOLEAN type and invalid default"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT,
                type=APP_SETTING_TYPE_BOOLEAN,
                default='abc',
            )

    def test_init_default_integer(self):
        """Test init with INTEGER type and valid default"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_INTEGER,
            default=0,
        )
        self.assertIsNotNone(s_def)

    def test_init_default_integer_as_string(self):
        """Test init with INTEGER type and valid default as string"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_INTEGER,
            default='0',
        )
        self.assertIsNotNone(s_def)

    def test_init_default_integer_invalid(self):
        """Test init with INTEGER type and invalid default"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT,
                type=APP_SETTING_TYPE_INTEGER,
                default='abc',
            )

    def test_init_default_json(self):
        """Test init with JSON type and valid default"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_JSON,
            default=DEF_JSON_VALUE,
        )
        self.assertIsNotNone(s_def)

    def test_init_default_json_empty_dict(self):
        """Test init with JSON type and valid empty dict default"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_JSON,
            default={},
        )
        self.assertIsNotNone(s_def)

    def test_init_default_json_empty_list(self):
        """Test init with JSON type and valid empty list default"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_JSON,
            default=[],
        )
        self.assertIsNotNone(s_def)

    def test_init_default_json_invalid(self):
        """Test init with JSON type and invalid default"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT,
                type=APP_SETTING_TYPE_JSON,
                default='{"x": "y"}',
            )

    def test_init_callable_default(self):
        """Test init with callable default"""

        def callable_default(project, user):
            return True

        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_STRING,
            default=callable_default,
        )
        self.assertIsNotNone(s_def)

    def test_init_callable_options(self):
        """Test init with callable options"""

        def callable_options(project, user):
            return [1, 2]

        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_INTEGER,
            default=1,
            options=callable_options,
        )
        self.assertIsNotNone(s_def)

    def test_init_default_not_in_options(self):
        """Test init with default value not in options"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT,
                type=APP_SETTING_TYPE_INTEGER,
                default=0,
                options=[1, 2],
            )

    def test_init_project_user_modifiable_false(self):
        """Test init with PROJECT_USER scope and user_modifiable=False"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT_USER,
            type=APP_SETTING_TYPE_BOOLEAN,
            default=True,
            user_modifiable=False,
        )
        self.assertIsNotNone(s_def)
        self.assertEqual(s_def.user_modifiable, False)

    def test_init_project_user_modifiable_unset(self):
        """Test init with PROJECT_USER scope and user_modifiable unset"""
        s_def = PluginAppSettingDef(
            name=DEF_NAME,
            scope=APP_SETTING_SCOPE_PROJECT_USER,
            type=APP_SETTING_TYPE_BOOLEAN,
            default=True,
        )
        self.assertIsNotNone(s_def)
        self.assertEqual(s_def.user_modifiable, False)

    def test_init_project_user_modifiable_true(self):
        """Test init with PROJECT_USER scope and user_modifiable=True"""
        with self.assertRaises(ValueError):
            PluginAppSettingDef(
                name=DEF_NAME,
                scope=APP_SETTING_SCOPE_PROJECT_USER,
                type=APP_SETTING_TYPE_BOOLEAN,
                default=True,
                user_modifiable=True,
            )
