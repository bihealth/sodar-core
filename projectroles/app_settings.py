"""Projectroles app settings API"""

import json
import logging

from typing import Any, Optional, Union

from django.conf import settings

from djangoplugins.point import PluginPoint

from projectroles.models import AppSetting, Project, SODARUser, SODAR_CONSTANTS
from projectroles.plugins import PluginAppSettingDef, PluginAPI
from projectroles.utils import get_display_name


logger = logging.getLogger(__name__)
plugin_api = PluginAPI()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
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
APP_SETTING_GLOBAL_DEFAULT = False
APP_SETTING_DEFAULT_VALUES = {
    APP_SETTING_TYPE_BOOLEAN: False,
    APP_SETTING_TYPE_INTEGER: 0,
    APP_SETTING_TYPE_JSON: {},
    APP_SETTING_TYPE_STRING: '',
}
APP_SETTING_SCOPE_ARGS = {
    APP_SETTING_SCOPE_PROJECT: {'project': True, 'user': False},
    APP_SETTING_SCOPE_USER: {'project': False, 'user': True},
    APP_SETTING_SCOPE_PROJECT_USER: {'project': True, 'user': True},
    APP_SETTING_SCOPE_SITE: {'project': False, 'user': False},
}
PROJECT_LIST_PAGE_OPTIONS = [10, 25, 50, 100, (-1, 'No pagination')]
DELETE_SCOPE_ERR_MSG = 'Argument "{arg}" must be set for {scope} scope setting'
GLOBAL_PROJECT_ERR_MSG = (
    'Overriding global settings for remote projects not allowed'
)
GLOBAL_USER_ERR_MSG = (
    'Overriding global user settings on target site not allowed'
)


# Define App Settings for projectroles app
PROJECTROLES_APP_SETTINGS = [
    PluginAppSettingDef(
        name='ip_restrict',
        scope=APP_SETTING_SCOPE_PROJECT,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=False,
        label='IP restrict',
        description='Restrict project access to the IP allow list',
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='ip_allow_list',
        scope=APP_SETTING_SCOPE_PROJECT,
        type=APP_SETTING_TYPE_STRING,
        label='IP allow list',
        description='Comma-separated list of allowed IPs for project access',
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='project_star',
        scope=APP_SETTING_SCOPE_PROJECT_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=False,
        global_edit=False,
        project_types=[PROJECT_TYPE_PROJECT, PROJECT_TYPE_CATEGORY],
    ),
    PluginAppSettingDef(
        name='notify_alert_project',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=True,
        label='Receive alerts for {} updates'.format(
            get_display_name(PROJECT_TYPE_PROJECT)
        ),
        description=(
            'Receive UI alerts for {} or {} creation, updating, moving, '
            'archiving and deletion.'.format(
                get_display_name(PROJECT_TYPE_CATEGORY),
                get_display_name(PROJECT_TYPE_PROJECT),
            )
        ),
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='notify_email_project',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=True,
        label='Receive email for {} updates'.format(
            get_display_name(PROJECT_TYPE_PROJECT)
        ),
        description=(
            'Receive email notifications for {} or {} creation, updating, '
            'moving, archiving and deletion.'.format(
                get_display_name(PROJECT_TYPE_CATEGORY),
                get_display_name(PROJECT_TYPE_PROJECT),
            )
        ),
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='notify_alert_role',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=True,
        label='Receive alerts for {} membership updates'.format(
            get_display_name(PROJECT_TYPE_PROJECT)
        ),
        description=(
            'Receive UI alerts for {} or {} membership updates and invitation '
            'activity.'.format(
                get_display_name(PROJECT_TYPE_CATEGORY),
                get_display_name(PROJECT_TYPE_PROJECT),
            )
        ),
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='notify_email_role',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=True,
        label='Receive email for {} membership updates'.format(
            get_display_name(PROJECT_TYPE_PROJECT)
        ),
        description=(
            'Receive email notifications for {} or {} membership updates and '
            'invitation activity.'.format(
                get_display_name(PROJECT_TYPE_CATEGORY),
                get_display_name(PROJECT_TYPE_PROJECT),
            )
        ),
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='site_read_only',
        scope=APP_SETTING_SCOPE_SITE,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=False,
        label='Site read-only mode',
        description='Set site in read-only mode. Data altering operations will '
        'be prohibited. Mode must be explicitly unset to allow data '
        'modification.',
        user_modifiable=True,
        global_edit=False,
    ),
    PluginAppSettingDef(
        name='project_list_highlight',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=True,
        label='Project list title highlight',
        description='Highlight project title in paths displayed in the project '
        'list.',
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='project_list_home_starred',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=False,
        label='Home view project list starred display',
        description='Initial starred mode to display in home view project list',
        user_modifiable=False,  # Editable only in project list
        global_edit=False,
    ),
    PluginAppSettingDef(
        name='project_list_pagination',
        scope=APP_SETTING_SCOPE_USER,
        type=APP_SETTING_TYPE_INTEGER,
        default=10,
        label='Project list page size',
        description='Amount of projects per page in the project list.',
        options=PROJECT_LIST_PAGE_OPTIONS,
        user_modifiable=True,
        global_edit=True,
    ),
    PluginAppSettingDef(
        name='project_access_block',
        scope=APP_SETTING_SCOPE_PROJECT,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=False,
        label='Block project access',
        description='Temporarily block all user access to project.',
        user_modifiable=False,  # Only allow modification by superuser
        global_edit=False,
        project_types=[PROJECT_TYPE_PROJECT],
    ),
    PluginAppSettingDef(
        name='category_public_stats',
        scope=APP_SETTING_SCOPE_PROJECT,
        type=APP_SETTING_TYPE_BOOLEAN,
        default=False,
        label='Display public category statistics',
        description='Enable all users to view {} readme and statistics. '
        'Limited to top level {}.'.format(
            get_display_name(PROJECT_TYPE_CATEGORY),
            get_display_name(PROJECT_TYPE_CATEGORY, plural=True),
        ),
        user_modifiable=True,  # Only allow modification by superuser
        global_edit=False,
        project_types=[PROJECT_TYPE_CATEGORY],
    ),
]


class AppSettingAPI:
    @classmethod
    def _validate_project_and_user(
        cls, scope: str, project: Project, user: SODARUser
    ):
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
                'Project and/or user invalid for setting with {} scope '
                '(project={}, user={})'.format(
                    scope,
                    project.get_log_title() if project else None,
                    user.username if user else None,
                )
            )

    @classmethod
    def _validate_value_in_options(
        cls,
        setting_value: str,
        setting_options: Union[list, callable],
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Ensure setting_value is present in setting_options.

        :param setting_value: String
        :param setting_options: List of options
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
        elif setting_options:
            opts = [
                o[0] if isinstance(o, tuple) else o for o in setting_options
            ]
            if setting_value not in opts:
                raise ValueError(
                    'Choice "{}" not found in options ({})'.format(
                        setting_value, ', '.join(map(str, setting_options))
                    )
                )

    @classmethod
    def _get_app_plugin(cls, plugin_name: str) -> PluginPoint:
        """
        Return app plugin by name.

        :param plugin_name: Name of the app plugin (string)
        :return: App plugin object
        :raise: ValueError if plugin is not found with the name
        """
        plugin = plugin_api.get_app_plugin(plugin_name)
        if not plugin:
            raise ValueError(f'Plugin not found with name "{plugin_name}"')
        return plugin

    @classmethod
    def _get_defs(
        cls,
        plugin: Optional[PluginPoint] = None,
        plugin_name: Optional[str] = None,
    ) -> dict:
        """
        Get app setting definitions for a plugin.

        :param plugin: Plugin object or None
        :param plugin_name: Name of the app plugin (string or None)
        :return: Dict
        :raise: ValueError if args are not valid or plugin is not found
        """
        if not plugin and not plugin_name:
            raise ValueError('Plugin object and name both unset')
        if plugin_name == APP_NAME:
            return cls.get_projectroles_defs()
        if not plugin:
            plugin = cls._get_app_plugin(plugin_name)
        return {s.name: s for s in plugin.app_settings}

    @classmethod
    def _get_json_value(cls, value: Union[str, dict]) -> dict:
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
            json.dumps(value)  # Ensure this is valid
            return value
        except Exception:
            raise ValueError(f'Value is not valid JSON: {value}')

    @classmethod
    def _log_set_debug(
        cls,
        action: str,
        plugin_name: str,
        setting_name: str,
        value: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Helper method for logging setting changes in set() method.

        :param action: Action string (string)
        :param plugin_name: App plugin name (string)
        :param setting_name: Setting name (string)
        :param value: Setting value (string)
        :param project: Project object or None
        :param user: User object or None
        """
        extra_data = []
        if project:
            extra_data.append(f'project={project.sodar_uuid}')
        if user:
            extra_data.append(f'user={user.username}')
        logger.debug(
            '{} app setting: {}.{} = "{}"{}'.format(
                action,
                plugin_name,
                setting_name,
                value,
                ' ({})'.format('; '.join(extra_data)) if extra_data else '',
            )
        )

    @classmethod
    def get_default(
        cls,
        plugin_name: str,
        setting_name: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
        post_safe: bool = False,
    ) -> Any:
        """
        Get default setting value from an app plugin.

        :param plugin_name: App plugin name (string, equals "name" in plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: Setting value
        :raise: ValueError if app plugin is not found
        :raise: KeyError if nothing is found with setting_name
        """
        if plugin_name == APP_NAME:
            s_defs = cls.get_projectroles_defs()
        else:
            s_defs = cls._get_defs(plugin_name=plugin_name)
        if setting_name not in s_defs:
            raise KeyError(
                f'Setting "{setting_name}" not found in app plugin '
                f'"{plugin_name}"'
            )
        s_def = s_defs[setting_name]
        if callable(s_def.default):
            try:
                return s_def.default(project, user)
            except Exception:
                logger.error(
                    f'Error in callable setting "{setting_name}" for plugin '
                    f'"{plugin_name}"'
                )
                return APP_SETTING_DEFAULT_VALUES[s_def.type]
        elif s_def.type == APP_SETTING_TYPE_JSON:
            if s_def.default is None:
                return {}
            if post_safe:
                return json.dumps(s_def.default)
        return s_def.default

    @classmethod
    def get(
        cls,
        plugin_name: str,
        setting_name: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
        post_safe: bool = False,
    ) -> Any:
        """
        Return app setting value for a project or a user. If not set, return
        default.

        :param plugin_name: App plugin name (string, equals "name" in plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: Value
        :raise: KeyError if nothing is found with setting_name
        """
        if not user or user.is_authenticated:
            try:
                val = AppSetting.objects.get_setting_value(
                    plugin_name, setting_name, project=project, user=user
                )
            except AppSetting.DoesNotExist:
                val = cls.get_default(
                    plugin_name,
                    setting_name,
                    project=project,
                    user=user,
                    post_safe=post_safe,
                )
        else:  # Anonymous user
            val = cls.get_default(
                plugin_name,
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
    def get_all_by_scope(
        cls,
        scope: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
        post_safe: bool = False,
    ) -> dict:
        """
        Return all setting values by scope. If a value is not set, return the
        default.

        :param scope: String
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        :raise: ValueError if scope or project and user args are invalid
        """
        PluginAppSettingDef.validate_scope(scope)
        cls._validate_project_and_user(scope, project, user)
        ret = {}
        all_defs = cls.get_all_defs()
        for plugin_name, s_defs in all_defs.items():
            for s_def in [d for d in s_defs.values() if d.scope == scope]:
                ret[f'settings.{plugin_name}.{s_def.name}'] = cls.get(
                    plugin_name, s_def.name, project, user, post_safe
                )
        return ret

    @classmethod
    def get_defaults(
        cls,
        scope: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
        post_safe: bool = False,
    ) -> dict:
        """
        Get all default settings for a scope.

        :param scope: Setting scope (PROJECT, USER or PROJECT_USER)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        """
        PluginAppSettingDef.validate_scope(scope)
        ret = {}
        app_plugins = plugin_api.get_active_plugins()

        for plugin in app_plugins:
            p_defs = cls.get_definitions(scope, plugin=plugin)
            for s_key in p_defs:
                ret[f'settings.{plugin.name}.{s_key}'] = cls.get_default(
                    plugin.name,
                    s_key,
                    project=project,
                    user=user,
                    post_safe=post_safe,
                )

        p_defs = cls.get_definitions(scope, plugin_name=APP_NAME)
        for s_key in p_defs:
            ret[f'settings.{APP_NAME}.{s_key}'] = cls.get_default(
                APP_NAME,
                s_key,
                project=project,
                user=user,
                post_safe=post_safe,
            )
        return ret

    @classmethod
    def set(
        cls,
        plugin_name: str,
        setting_name: str,
        value: Any,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
        validate: bool = True,
    ) -> bool:
        """
        Set value of an existing project or user settings. Creates the object if
        not found.

        :param plugin_name: App plugin name (string, equals "name" in plugin)
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
        s_def = cls.get_definition(name=setting_name, plugin_name=plugin_name)
        cls._validate_project_and_user(s_def.scope, project, user)
        # Check project type
        if project and project.type not in s_def.project_types:
            raise ValueError(
                f'Project type {project.type} not allowed for setting '
                f'{setting_name}'
            )
        # Prevent updating global setting on target site
        if s_def.global_edit:
            if project and project.is_remote():
                raise ValueError(GLOBAL_PROJECT_ERR_MSG)
            if (
                user
                and not project
                and settings.PROJECTROLES_SITE_MODE == SITE_MODE_TARGET
            ):
                raise ValueError(GLOBAL_USER_ERR_MSG)

        # TODO: Refactor and remove repetition
        try:  # Update existing setting
            q_kwargs = {'name': setting_name, 'project': project, 'user': user}
            if not plugin_name == APP_NAME:
                q_kwargs['app_plugin__name'] = plugin_name
            else:
                q_kwargs['app_plugin'] = None
            setting = AppSetting.objects.get(**q_kwargs)
            if cls.compare_value(setting, value):
                return False
            v = (
                cls._get_json_value(value)
                if setting.type == APP_SETTING_TYPE_JSON
                else value
            )
            if validate:
                cls.validate(
                    setting.type,
                    v,
                    s_def.options,
                    project=project,
                    user=user,
                )
            if setting.type == APP_SETTING_TYPE_JSON:
                setting.value_json = v
            else:
                setting.value = v
            setting.save()
            cls._log_set_debug(
                'Set', plugin_name, setting_name, value, project, user
            )
            return True

        except AppSetting.DoesNotExist:  # Create new
            s_type = s_def.type
            if plugin_name == APP_NAME:
                app_plugin_model = None
            else:
                app_plugin = cls._get_app_plugin(plugin_name)
                app_plugin_model = app_plugin.get_model()
            if validate:
                v = (
                    cls._get_json_value(value)
                    if s_type == APP_SETTING_TYPE_JSON
                    else value
                )
                cls.validate(
                    s_type,
                    v,
                    s_def.options,
                    project=project,
                    user=user,
                )
            s_mod = bool(s_def.user_modifiable)
            s_vals = {
                'app_plugin': app_plugin_model,
                'project': project,
                'user': user,
                'name': setting_name,
                'type': s_type,
                'user_modifiable': s_mod,
            }
            if s_type == APP_SETTING_TYPE_JSON:
                s_vals['value_json'] = cls._get_json_value(value)
            else:
                s_vals['value'] = value
            AppSetting.objects.create(**s_vals)
            cls._log_set_debug(
                'Create', plugin_name, setting_name, value, project, user
            )
            return True

    @classmethod
    def is_set(
        cls,
        plugin_name: str,
        setting_name: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ) -> bool:
        """
        Return True if the setting has been set, instead of retrieving the
        default value from the definition.

        NOTE: Also returns True if the current set value equals the default.

        :param plugin_name: App plugin name (string, equals "name" in plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (optional)
        :param user: User object (optional)
        :return: Boolean
        """
        s_def = cls.get_definition(name=setting_name, plugin_name=plugin_name)
        cls._validate_project_and_user(s_def.scope, project, user)
        q_kwargs = {'name': setting_name, 'project': project, 'user': user}
        if not plugin_name == APP_NAME:
            q_kwargs['app_plugin__name'] = plugin_name
        else:
            q_kwargs['app_plugin'] = None
        return AppSetting.objects.filter(**q_kwargs).exists()

    @classmethod
    def delete(
        cls,
        plugin_name: str,
        setting_name: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Delete one or more app setting objects. In case of a PROJECT_USER
        setting, can be used to delete all settings related to project.

        :param plugin_name: App plugin name (string, equals "name" in plugin)
        :param setting_name: Setting name (string)
        :param project: Project object to delete setting from (optional)
        :param user: User object to delete setting from (optional)
        :raise: ValueError with invalid project/user args
        """
        s_def = cls.get_definition(setting_name, plugin_name=plugin_name)
        if s_def.scope != APP_SETTING_SCOPE_PROJECT_USER:
            cls._validate_project_and_user(s_def.scope, project, user)
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
                plugin_name, setting_name, '; '.join(q_kwargs)
            )
        )
        app_settings = AppSetting.objects.filter(**q_kwargs)
        sc = app_settings.count()
        app_settings.delete()
        logger.debug(
            'Deleted {} app setting{}'.format(sc, 's' if sc != 1 else '')
        )

    @classmethod
    def delete_by_scope(
        cls,
        scope: str,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Delete all app settings within a given scope for a project and/or user.

        :param scope: Setting scope (string)
        :param project: Project object to delete setting from
        :param user: User object to delete setting from
        :raise: ValueError if scope, project or user are incorrect
        """
        PluginAppSettingDef.validate_scope(scope)
        cls._validate_project_and_user(scope, project, user)
        for plugin_name, app_settings in cls.get_all_defs().items():
            for s_name, s_def in app_settings.items():
                if s_def.scope == scope:
                    cls.delete(plugin_name, s_name, project=project, user=user)

    @classmethod
    def validate(
        cls,
        setting_type: str,
        setting_value: Any,
        setting_options: Union[callable, None, list],
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ) -> bool:
        """
        Validate setting value according to its type.

        :param setting_type: Setting type (string)
        :param setting_value: Setting value
        :param setting_options: Setting options (can be None)
        :param project: Project object (optional)
        :param user: User object (optional)
        :raise: ValueError if setting_type or setting_value is invalid
        """
        PluginAppSettingDef.validate_type(setting_type)
        cls._validate_value_in_options(
            setting_value, setting_options, project=project, user=user
        )
        # Test callable value
        if callable(setting_value):
            setting_value(project, user)
        else:  # Else validate normal value
            PluginAppSettingDef.validate_value(setting_type, setting_value)
        return True

    @classmethod
    def get_definition(
        cls,
        name: str,
        plugin: Optional[PluginPoint] = None,
        plugin_name: Optional[str] = None,
    ) -> dict:
        """
        Return definition for a single app setting, either based on an app name
        or the plugin object.

        :param name: Setting name (string)
        :param plugin: Plugin object or None
        :param plugin_name: Name of the app plugin (string or None)
        :return: Dict
        :raise: ValueError if neither plugin_name nor plugin are set, or if
                setting is not found in plugin
        """
        defs = cls._get_defs(plugin, plugin_name)
        if name not in defs:
            raise ValueError(
                f'App setting not found in plugin '
                f'"{plugin_name or plugin.name}" with name "{name}"'
            )
        return defs[name]

    @classmethod
    def get_definitions(
        cls,
        scope: Optional[str] = None,
        plugin: Optional[PluginPoint] = None,
        plugin_name: Optional[str] = None,
        user_modifiable: bool = False,
    ) -> dict:
        """
        Return app setting definitions from a plugin, optionally limited by
        scope.

        :param scope: String or None
        :param plugin: Plugin object or None
        :param plugin_name: App plugin name (string, equals "name" in plugin)
        :param user_modifiable: Only return non-superuser modifiable settings if
                                True (boolean)
        :return: Dict
        :raise: ValueError if scope is invalid or if neither plugin_name nor
                plugin are set
        """
        if scope:
            PluginAppSettingDef.validate_scope(scope)
        defs = cls._get_defs(plugin, plugin_name)
        return {
            k: v
            for k, v in defs.items()
            if (not scope or v.scope == scope)
            and (not user_modifiable or v.user_modifiable)
        }

    @classmethod
    def get_projectroles_defs(cls) -> dict:
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
        return {s.name: s for s in app_settings}

    @classmethod
    def get_all_defs(cls) -> dict:
        """
        Return app setting definitions for projectroles and all active app
        plugins in a dictionary with the app name as key.

        :return: Dict
        """
        ret = {APP_NAME: cls.get_projectroles_defs()}
        plugins = (
            []
            + plugin_api.get_active_plugins('project_app')
            + plugin_api.get_active_plugins('site_app')
        )
        for p in plugins:
            ret[p.name] = cls._get_defs(p)
        return ret

    @classmethod
    def compare_value(cls, obj: AppSetting, input_value: Any) -> bool:
        """
        Compare input value to value in an AppSetting object. Return True if
        values match, False if there is a mismatch.

        :param obj: AppSetting object
        :param input_value: Input value (string, int, bool or dict)
        :return: Bool
        """
        if obj.type == APP_SETTING_TYPE_JSON:
            return (
                not obj.value_json and not input_value
            ) or obj.value_json == cls._get_json_value(input_value)
        elif obj.type == APP_SETTING_TYPE_BOOLEAN:
            if isinstance(input_value, str):
                input_value = bool(int(input_value))
            return bool(int(obj.value)) == input_value
        return obj.value == str(input_value)


def get_example_setting_default(
    project: Optional[Project] = None, user: Optional[SODARUser] = None
) -> str:
    """
    Example method for callable default value retrieval for app settings.

    :param project: Project object
    :param user: User object
    :return: String with project and user info or 'No project'
    """
    response = 'N/A'
    if project and user:
        response = f'{project.title}:{user.username}'
    elif project:
        response = str(project.sodar_uuid)
    elif user:
        response = str(user.sodar_uuid)
    return response


def get_example_setting_options(
    project: Optional[Project] = None, user: Optional[SODARUser] = None
) -> list[tuple]:
    """
    Example method for callable option list retrieval for app settings.

    :param project: Project object
    :param user: User object
    :return: List of tuples for ChoiceField
    """
    ret = [('N/A', 'No project or user for callable'), 'Example string option']
    if project and user:
        ret.append(
            (
                str(project.sodar_uuid),
                f'Project UUID {project.sodar_uuid} by {user.username}',
            )
        )
    elif project:
        ret.append(
            (
                str(project.sodar_uuid),
                f'Project UUID: {project.sodar_uuid}',
            )
        )
    elif user:
        ret.append((str(user.sodar_uuid), f'User UUID: {user.sodar_uuid}'))
    return ret
