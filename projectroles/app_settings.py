"""Projectroles app settings API"""

import json
import logging

from django.conf import settings

from projectroles.models import AppSetting, APP_SETTING_TYPES, SODAR_CONSTANTS
from projectroles.plugins import get_app_plugin, get_active_plugins


logger = logging.getLogger(__name__)


# SODAR constants
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]
APP_SETTING_SCOPE_SITE = SODAR_CONSTANTS['APP_SETTING_SCOPE_SITE']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']

# Local constants
APP_SETTING_LOCAL_DEFAULT = True
APP_SETTING_SCOPES = [
    APP_SETTING_SCOPE_PROJECT,
    APP_SETTING_SCOPE_USER,
    APP_SETTING_SCOPE_PROJECT_USER,
    APP_SETTING_SCOPE_SITE,
]
APP_SETTING_DEFAULT_VALUES = {
    'STRING': '',
    'INTEGER': 0,
    'BOOLEAN': False,
    'JSON': {},
}
APP_SETTING_SCOPE_ARGS = {
    APP_SETTING_SCOPE_PROJECT: {'project': True, 'user': False},
    APP_SETTING_SCOPE_USER: {'project': False, 'user': True},
    APP_SETTING_SCOPE_PROJECT_USER: {'project': True, 'user': True},
    APP_SETTING_SCOPE_SITE: {'project': False, 'user': False},
}
DELETE_SCOPE_ERR_MSG = 'Argument "{arg}" must be set for {scope} scope setting'
OVERRIDE_ERR_MSG = 'Overriding global settings for remote projects not allowed'


# Define App Settings for projectroles app
PROJECTROLES_APP_SETTINGS = {
    #: App settings definition
    #:
    #: Example ::
    #:
    #:     'example_setting': {
    #:         'scope': 'PROJECT',  # PROJECT/USER/PROJECT-USER/SITE
    #:         'type': 'STRING',  # STRING/INTEGER/BOOLEAN/JSON
    #:         'default': 'example',
    #:         'label': 'Project setting',  # Optional, defaults to name/key
    #:         'placeholder': 'Enter example setting here',  # Optional
    #:         'description': 'Example project setting',  # Optional
    #:         'options': ['example', 'example2'],  # Optional, only for
    #:                    settings of type STRING or INTEGER
    #:         'user_modifiable': True,  # Optional, show/hide in forms
    #:         'local': False,  # Allow editing in target site forms if True
    #:         'project_types': [PROJECT_TYPE_PROJECT],  # Optional, list may
    #:          contain PROJECT_TYPE_CATEGORY and/or PROJECT_TYPE_PROJECT
    #:     }
    'ip_restrict': {
        'scope': APP_SETTING_SCOPE_PROJECT,
        'type': 'BOOLEAN',
        'default': False,
        'label': 'IP restrict',
        'description': 'Restrict project access by an allowed IP list',
        'user_modifiable': True,
        'local': False,
    },
    'ip_allowlist': {
        'scope': APP_SETTING_SCOPE_PROJECT,
        'type': 'JSON',
        'default': [],
        'label': 'IP allow list',
        'description': 'List of allowed IPs for project access',
        'user_modifiable': True,
        'local': False,
    },
    'user_email_additional': {
        'scope': APP_SETTING_SCOPE_USER,
        'type': 'STRING',
        'default': '',
        'placeholder': 'email1@example.com;email2@example.com',
        'label': 'Additional email',
        'description': 'Also send user emails to these addresses. Separate '
        'multiple emails with semicolon.',
        'user_modifiable': True,
        'local': False,
        'project_types': [PROJECT_TYPE_PROJECT],
    },
    'project_star': {
        'scope': APP_SETTING_SCOPE_PROJECT_USER,
        'type': 'BOOLEAN',
        'default': False,
        'local': True,
        'project_types': [PROJECT_TYPE_PROJECT, PROJECT_TYPE_CATEGORY],
    },
}


class AppSettingAPI:
    @classmethod
    def _check_project_and_user(cls, scope, project, user):
        """
        Ensure project and user parameters are set according to scope.

        :param scope: Scope of Setting (USER, PROJECT, PROJECT_USER, SITE)
        :param project: Project object
        :param user: User object
        :raise: ValueError if none or both objects exist
        """
        if not APP_SETTING_SCOPE_ARGS[scope] == {
            'project': project is not None,
            'user': user is not None,
        }:
            raise ValueError(
                'Project and/or user are set incorrect for setting '
                'with {} scope'.format(scope)
            )

    @classmethod
    def _check_scope(cls, scope):
        """
        Ensure the validity of a scope definition.

        :param scope: String
        :raise: ValueError if scope is not recognized
        """
        if scope not in APP_SETTING_SCOPES:
            raise ValueError('Invalid scope "{}"'.format(scope))

    @classmethod
    def _check_type(cls, setting_type):
        """
        Ensure the validity of app setting type.

        :param setting_type: String
        :raise: ValueError if type is not recognized
        """
        if setting_type not in APP_SETTING_TYPES:
            raise ValueError('Invalid setting type "{}"'.format(setting_type))

    @classmethod
    def _check_type_options(cls, setting_type, setting_options):
        """
        Ensure setting_type is allowed to have options.

        :param setting_type: String
        :param setting_options: List of options (Strings or Integers)
        :raise: ValueError if type is not recognized
        """
        if setting_type not in ['INTEGER', 'STRING'] and setting_options:
            raise ValueError(
                'Options are only allowed for settings of type INTEGER and '
                'STRING'
            )

    @classmethod
    def _check_value_in_options(
        cls, setting_value, setting_options, project=None, user=None
    ):
        """
        Ensure setting_value is present in setting_options.

        :param setting_value: String
        :param setting_options: List of options (String or Integers)
        :param project: Project object
        :param user: User object
        :raise: ValueError if type is not recognized
        """
        if callable(setting_options):
            valid_options = [
                val[0] if isinstance(val, tuple) else val
                for val in setting_options(project, user)
            ]
            if setting_value not in valid_options:
                raise ValueError(
                    'Choice "{}" not found in options ({})'.format(
                        setting_value,
                        ', '.join(map(str, valid_options)),
                    )
                )
        elif (
            setting_options
            and not callable(setting_options)
            and setting_value not in setting_options
        ):
            raise ValueError(
                'Choice "{}" not found in options ({})'.format(
                    setting_value, ', '.join(map(str, setting_options))
                )
            )

    @classmethod
    def _get_app_plugin(cls, app_name):
        """
        Return app plugin by name.

        :param app_name: Name of the app plugin (string or None)
        :return: App plugin object
        :raise: ValueError if plugin is not found with the name
        """
        plugin = get_app_plugin(app_name)
        if not plugin:
            raise ValueError(
                'Plugin not found with app name "{}"'.format(app_name)
            )
        return plugin

    @classmethod
    def _get_defs(cls, plugin=None, app_name=None):
        """
        Ensure valid argument values for a settings def query.

        :param plugin: Plugin object or None
        :param app_name: Name of the app plugin (string or None)
        :return: Dict
        :raise: ValueError if args are not valid or plugin is not found
        """
        if not plugin and not app_name:
            raise ValueError('Plugin and app name both unset')
        if app_name == 'projectroles':
            return cls.get_projectroles_defs()
        if not plugin:
            plugin = cls._get_app_plugin(app_name)
        return plugin.app_settings

    @classmethod
    def _get_json_value(cls, value):
        """
        Return JSON value as dict regardless of input type

        :param value: Original value (string or dict)
        :raise: json.decoder.JSONDecodeError if string value is not valid JSON
        :raise: ValueError if value type is not recognized or if value is not
                valid JSON
        :return: dict
        """
        if not value:
            return {}
        try:
            if isinstance(value, str):
                return json.loads(value)
            else:
                json.dumps(value)  # Ensure this is valid
                return value
        except Exception:
            raise ValueError('Value is not valid JSON: {}'.format(value))

    @classmethod
    def _compare_value(cls, obj, input_value):
        """
        Compare input value to value in an AppSetting object. Return True if
        values match, False if there is a mismatch.

        :param obj: AppSetting object
        :param input_value: Input value (string, int, bool or dict)
        :return: Bool
        """
        if obj.type == 'JSON':
            return (
                not obj.value_json and not input_value
            ) or obj.value_json == cls._get_json_value(input_value)
        elif obj.type == 'BOOLEAN':
            return bool(int(obj.value)) == input_value
        return obj.value == str(input_value)

    @classmethod
    def _log_set_debug(
        cls, action, app_name, setting_name, value, project, user
    ):
        """
        Helper method for logging setting changes in set() method.

        :param action: Action string (string)
        :param app_name: Plugin app name (string)
        :param setting_name: Setting name (string)
        :param value: Setting value (string)
        :param project: Project object
        :param user: User object
        """
        extra_data = []
        if project:
            extra_data.append('project={}'.format(project.sodar_uuid))
        if user:
            extra_data.append('user={}'.format(user.username))
        logger.debug(
            '{} app setting: {}.{} = "{}"{}'.format(
                action,
                app_name,
                setting_name,
                value,
                ' ({})'.format('; '.join(extra_data)) if extra_data else '',
            )
        )

    @classmethod
    def get_default(
        cls, app_name, setting_name, project=None, user=None, post_safe=False
    ):
        """
        Get default setting value from an app plugin.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: Setting value (string, integer or boolean)
        :raise: ValueError if app plugin is not found
        :raise: KeyError if nothing is found with setting_name
        """
        if app_name == 'projectroles':
            app_settings = cls.get_projectroles_defs()
        else:
            app_plugin = get_app_plugin(app_name)
            if not app_plugin:
                raise ValueError('App plugin not found: "{}"'.format(app_name))
            app_settings = app_plugin.app_settings

        if setting_name in app_settings:
            if callable(app_settings[setting_name].get('default')):
                try:
                    callable_setting = app_settings[setting_name]['default']
                    return callable_setting(project, user)
                except Exception:
                    logger.error(
                        'Error in callable setting "{}" for app "{}"'.format(
                            setting_name, app_name
                        )
                    )
                    return APP_SETTING_DEFAULT_VALUES[
                        app_settings[setting_name]['type']
                    ]
            elif app_settings[setting_name]['type'] == 'JSON':
                json_default = app_settings[setting_name].get('default')
                if not json_default:
                    if isinstance(json_default, dict):
                        return {}
                    elif isinstance(json_default, list):
                        return []
                    return {}
                if post_safe:
                    return json.dumps(app_settings[setting_name]['default'])
            return app_settings[setting_name]['default']

        raise KeyError(
            'Setting "{}" not found in app plugin "{}"'.format(
                setting_name, app_name
            )
        )

    @classmethod
    def get(
        cls, app_name, setting_name, project=None, user=None, post_safe=False
    ):
        """
        Return app setting value for a project or a user. If not set, return
        default.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: String or None
        :raise: KeyError if nothing is found with setting_name
        """
        if not user or user.is_authenticated:
            try:
                val = AppSetting.objects.get_setting_value(
                    app_name, setting_name, project=project, user=user
                )
            except AppSetting.DoesNotExist:
                val = cls.get_default(
                    app_name,
                    setting_name,
                    project=project,
                    user=user,
                    post_safe=post_safe,
                )
        else:  # Anonymous user
            val = cls.get_default(
                app_name,
                setting_name,
                project=project,
                user=user,
                post_safe=post_safe,
            )
        # Handle post_safe for dict values (JSON)
        if post_safe and isinstance(val, (dict, list)):
            return json.dumps(val)
        return val

    @classmethod
    def get_all(cls, project=None, user=None, post_safe=False):
        """
        Return all setting values. If the value is not found, return
        the default.

        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        :raise: ValueError if neither project nor user are set
        """
        if not project and not user:
            raise ValueError('Project and user are both unset')

        ret = {}
        app_plugins = get_active_plugins()
        for plugin in app_plugins:
            p_settings = cls.get_definitions(
                APP_SETTING_SCOPE_PROJECT, plugin=plugin
            )
            for s_key in p_settings:
                ret['settings.{}.{}'.format(plugin.name, s_key)] = cls.get(
                    plugin.name, s_key, project, user, post_safe
                )

        p_settings = cls.get_definitions(
            APP_SETTING_SCOPE_PROJECT, app_name='projectroles'
        )
        for s_key in p_settings:
            ret['settings.{}.{}'.format('projectroles', s_key)] = cls.get(
                'projectroles', s_key, post_safe
            )
        return ret

    @classmethod
    def get_defaults(cls, scope, project=None, user=None, post_safe=False):
        """
        Get all default settings for a scope.

        :param scope: Setting scope (PROJECT, USER or PROJECT_USER)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        """
        cls._check_scope(scope)
        ret = {}
        app_plugins = get_active_plugins()

        for plugin in app_plugins:
            p_settings = cls.get_definitions(scope, plugin=plugin)
            for s_key in p_settings:
                ret[
                    'settings.{}.{}'.format(plugin.name, s_key)
                ] = cls.get_default(
                    plugin.name,
                    s_key,
                    project=project,
                    user=user,
                    post_safe=post_safe,
                )

        p_settings = cls.get_definitions(scope, app_name='projectroles')
        for s_key in p_settings:
            ret[
                'settings.{}.{}'.format('projectroles', s_key)
            ] = cls.get_default(
                'projectroles',
                s_key,
                project=project,
                user=user,
                post_safe=post_safe,
            )
        return ret

    @classmethod
    def set(
        cls,
        app_name,
        setting_name,
        value,
        project=None,
        user=None,
        validate=True,
    ):
        """
        Set value of an existing project or user settings. Creates the object if
        not found.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param value: Value to be set
        :param project: Project object (optional)
        :param user: User object (optional)
        :param validate: Validate value (bool, default=True)
        :return: True if changed, False if not changed
        :raise: ValueError if validating and value is not accepted for setting
                type
        :raise: ValueError if neither project nor user are set
        :raise: KeyError if setting name is not found in plugin specification
        """
        s_def = cls.get_definition(name=setting_name, app_name=app_name)
        cls._check_scope(s_def.get('scope', None))
        cls._check_project_and_user(s_def.get('scope', None), project, user)
        # Check project type
        if (
            project
            and not s_def.get('project_types', None)
            and not project.type == PROJECT_TYPE_PROJECT
            or project
            and s_def.get('project_types', None)
            and project.type not in s_def['project_types']
        ):
            raise ValueError(
                'Project type {} not allowed for setting {}'.format(
                    project.type, setting_name
                )
            )
        # Prevent updating global setting on remote project
        # TODO: Prevent editing global USER settings (#1329)
        if (
            not s_def.get('local', APP_SETTING_LOCAL_DEFAULT)
            and project
            and project.is_remote()
        ):
            raise ValueError(OVERRIDE_ERR_MSG)

        try:  # Update existing setting
            q_kwargs = {'name': setting_name, 'project': project, 'user': user}
            if not app_name == 'projectroles':
                q_kwargs['app_plugin__name'] = app_name
            setting = AppSetting.objects.get(**q_kwargs)
            if cls._compare_value(setting, value):
                return False
            if validate:
                cls.validate(
                    setting.type,
                    value,
                    s_def.get('options'),
                    project=project,
                    user=user,
                )
            if setting.type == 'JSON':
                setting.value_json = cls._get_json_value(value)
            else:
                setting.value = value
            setting.save()
            cls._log_set_debug(
                'Set', app_name, setting_name, value, project, user
            )
            return True

        except AppSetting.DoesNotExist:  # Create new
            s_type = s_def['type']
            if app_name == 'projectroles':
                app_plugin_model = None
            else:
                app_plugin = get_app_plugin(app_name)
                app_plugin_model = app_plugin.get_model()
            if validate:
                v = cls._get_json_value(value) if s_type == 'JSON' else value
                cls.validate(
                    s_type,
                    v,
                    s_def.get('options'),
                    project=project,
                    user=user,
                )
            s_mod = (
                bool(s_def['user_modifiable'])
                if 'user_modifiable' in s_def
                else True
            )
            s_vals = {
                'app_plugin': app_plugin_model,
                'project': project,
                'user': user,
                'name': setting_name,
                'type': s_type,
                'user_modifiable': s_mod,
            }
            if s_type == 'JSON':
                s_vals['value_json'] = cls._get_json_value(value)
            else:
                s_vals['value'] = value
            AppSetting.objects.create(**s_vals)
            cls._log_set_debug(
                'Create', app_name, setting_name, value, project, user
            )
            return True

    @classmethod
    def delete(cls, app_name, setting_name, project=None, user=None):
        """
        Delete one or more app setting objects. In case of a PROJECT_USER
        setting, can be used to delete all settings related to project.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param project: Project object to delete setting from (optional)
        :param user: User object to delete setting from (optional)
        :raise: ValueError with invalid project/user args
        """
        setting_def = cls.get_definition(setting_name, app_name=app_name)
        if setting_def['scope'] != APP_SETTING_SCOPE_PROJECT_USER:
            cls._check_project_and_user(
                setting_def.get('scope', None), project, user
            )
        elif not project:
            raise ValueError(
                'Project must be set for {} scope settings'.format(
                    APP_SETTING_SCOPE_PROJECT_USER
                )
            )
        q_kwargs = {'name': setting_name}
        if user:
            q_kwargs['user'] = user
        if project:
            q_kwargs['project'] = project
        logger.debug(
            'Delete app setting: {}.{} ({})'.format(
                app_name, setting_name, '; '.join(q_kwargs)
            )
        )
        app_settings = AppSetting.objects.filter(**q_kwargs)
        s_count = app_settings.count()
        app_settings.delete()
        logger.debug(
            'Deleted {} app setting{}'.format(
                s_count, 's' if s_count != 1 else ''
            )
        )

    @classmethod
    def delete_by_scope(
        cls,
        scope,
        project=None,
        user=None,
    ):
        """
        Delete all app settings within a given scope for a project and/or user.

        :param scope: Setting scope (string)
        :param project: Project object to delete setting from
        :param user: User object to delete setting from
        :raise: ValueError if scope, project or user are incorrect
        """
        if not scope:
            raise ValueError('Scope must be set')
        cls._check_scope(scope)
        cls._check_project_and_user(scope, project, user)
        for app_name, app_settings in cls.get_all_defs().items():
            for setting_name, setting_def in app_settings.items():
                if setting_def['scope'] == scope:
                    cls.delete(
                        app_name,
                        setting_name,
                        project=project,
                        user=user,
                    )

    @classmethod
    def validate(
        cls,
        setting_type,
        setting_value,
        setting_options,
        project=None,
        user=None,
    ):
        """
        Validate setting value according to its type.

        :param setting_type: Setting type
        :param setting_value: Setting value
        :param setting_options: Setting options (can be None)
        :param project: Project object (optional)
        :param user: User object (optional)
        :raise: ValueError if setting_type or setting_value is invalid
        """
        cls._check_type(setting_type)
        cls._check_type_options(setting_type, setting_options)
        cls._check_value_in_options(
            setting_value, setting_options, project=project, user=user
        )

        # Check callable
        if callable(setting_value):
            setting_value(project, user)

        if setting_type == 'BOOLEAN':
            if not isinstance(setting_value, bool):
                raise ValueError(
                    'Please enter a valid boolean value ({})'.format(
                        setting_value
                    )
                )
        elif setting_type == 'INTEGER':
            if (
                not isinstance(setting_value, int)
                and not str(setting_value).isdigit()
            ):
                raise ValueError(
                    'Please enter a valid integer value ({})'.format(
                        setting_value
                    )
                )
        elif setting_type == 'JSON':
            try:
                json.dumps(setting_value)
            except TypeError:
                raise ValueError(
                    'Please enter valid JSON ({})'.format(setting_value)
                )
        return True

    @classmethod
    def get_definition(cls, name, plugin=None, app_name=None):
        """
        Return definition for a single app setting, either based on an app name
        or the plugin object.

        :param name: Setting name
        :param plugin: Plugin object or None
        :param app_name: Name of the app plugin (string or None)
        :return: Dict
        :raise: ValueError if neither app_name nor plugin are set or if setting
                is not found in plugin
        """
        defs = cls._get_defs(plugin, app_name)
        if name not in defs:
            raise ValueError(
                'App setting not found in app "{}" with name "{}"'.format(
                    app_name or plugin.name, name
                )
            )
        ret = defs[name]
        cls._check_type(ret['type'])
        cls._check_type_options(ret['type'], ret.get('options'))
        return ret

    @classmethod
    def get_definitions(
        cls,
        scope,
        plugin=None,
        app_name=None,
        user_modifiable=False,
    ):
        """
        Return app setting definitions of a specific scope from a plugin.

        :param scope: PROJECT, USER or PROJECT_USER
        :param plugin: Plugin object or None
        :param app_name: Name of the app plugin (string or None)
        :param user_modifiable: Only return non-superuser modifiable settings if
                                True (boolean)
        :return: Dict
        :raise: ValueError if scope is invalid or if neither app_name nor
                plugin are set
        """
        cls._check_scope(scope)
        defs = cls._get_defs(plugin, app_name)
        ret = {
            k: v
            for k, v in defs.items()
            if (
                'scope' in v
                and v['scope'] == scope
                and (
                    not user_modifiable
                    or (
                        'user_modifiable' not in v
                        or v['user_modifiable'] is True
                    )
                )
            )
        }
        # Ensure type validity
        for k, v in ret.items():
            cls._check_type(v['type'])
            cls._check_type_options(v['type'], v.get('options'))
        return ret

    @classmethod
    def get_projectroles_defs(cls):
        """
        Return projectroles settings definitions. If it exists, get value from
        settings.PROJECTROLES_APP_SETTINGS_TEST for testing modifications.

        :return: Dict
        """
        try:
            app_settings = (
                settings.PROJECTROLES_APP_SETTINGS_TEST
                or PROJECTROLES_APP_SETTINGS
            )
        except AttributeError:
            app_settings = PROJECTROLES_APP_SETTINGS
        for k, v in app_settings.items():
            if 'local' not in v:
                raise ValueError(
                    'Attribute "local" is missing in projectroles app '
                    'setting definition "{}"'.format(k)
                )
        return app_settings

    @classmethod
    def get_all_defs(cls):
        """
        Return app setting definitions for projectroles and all active app
        plugins in a dictionary with the app name as key.

        :return: Dict
        """
        ret = {'projectroles': cls.get_projectroles_defs()}
        plugins = (
            []
            + get_active_plugins('project_app')
            + get_active_plugins('site_app')
        )
        for p in plugins:
            ret[p.name] = p.app_settings
        return ret


def get_example_setting_default(project=None, user=None):
    """
    Example method for callable default value retrieval for app settings.

    :param project: Project object
    :param user: User object
    :return: String with project and user info or 'No project'
    """
    response = 'N/A'
    if project and user:
        response = '{}:{}'.format(project.title, user.username)
    elif project:
        response = str(project.sodar_uuid)
    elif user:
        response = str(user.sodar_uuid)
    return response


def get_example_setting_options(project=None, user=None):
    """
    Example method for callable option list retrieval for app settings.

    :param project: Project object
    :param user: User object
    :return: List of tuples for ChoiceField
    """
    response = [
        ('N/A', 'No project or user for callable'),
        'Example string option',
    ]
    if project and user:
        response.append(
            (
                str(project.sodar_uuid),
                'Project UUID {} by {}'.format(
                    project.sodar_uuid, user.username
                ),
            )
        )
    elif project:
        response.append(
            (
                str(project.sodar_uuid),
                'Project UUID: {}'.format(project.sodar_uuid),
            )
        )
    elif user:
        response.append(
            (str(user.sodar_uuid), 'User UUID: {}'.format(user.sodar_uuid))
        )
    return response
