"""Plugin point definitions and plugin API for apps based on projectroles"""

import json
import logging

from typing import Any, Optional, Union
from uuid import UUID

from django.conf import settings
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from djangoplugins.point import PluginPoint

from projectroles.models import (
    Project,
    Role,
    RoleAssignment,
    SODARUser,
    APP_SETTING_TYPES,
    SODAR_CONSTANTS,
)


logger = logging.getLogger(__name__)


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
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
PLUGIN_TYPES = {
    'project_app': 'ProjectAppPluginPoint',
    'backend': 'BackendPluginPoint',
    'site_app': 'SiteAppPluginPoint',
}
APP_SETTING_SCOPES = [
    APP_SETTING_SCOPE_PROJECT,
    APP_SETTING_SCOPE_USER,
    APP_SETTING_SCOPE_PROJECT_USER,
    APP_SETTING_SCOPE_SITE,
]
APP_SETTING_OPTION_TYPES = [APP_SETTING_TYPE_INTEGER, APP_SETTING_TYPE_STRING]
# TODO: Remove in v1.3 (see #1718)
PLUGIN_API_DEPRECATE_MSG = (
    'Importing and calling {method}() directly from projectroles.plugins has '
    'been deprecated and will be removed in v1.3. Use '
    'projectroles.plugins.PluginAPI instead.'
)

# From djangoplugins
ENABLED = 0
DISABLED = 1
REMOVED = 2


# Plugin Mixins ----------------------------------------------------------------


class ProjectModifyPluginMixin:
    """
    Mixin for project plugin API extensions for additional actions to be
    performed for project and role modifications. Used if e.g. updating external
    resources based on SODAR Core projects.

    Add this into your project app or backend plugin if you want to implement
    additional modification features. It is not supported on site app plugins.
    """

    def perform_project_modify(
        self,
        project: Project,
        action: str,
        project_settings: dict,
        old_data: Optional[dict] = None,
        old_settings: Optional[dict] = None,
        request: Optional[HttpRequest] = None,
    ):
        """
        Perform additional actions to finalize project creation or update.

        :param project: Current project object (Project)
        :param action: Action to perform (CREATE or UPDATE)
        :param project_settings: Project app settings (dict)
        :param old_data: Old project data in case of an update (dict or None)
        :param old_settings: Old app settings in case of update (dict or None)
        :param request: Request object or None
        """
        pass

    def revert_project_modify(
        self,
        project: Project,
        action: str,
        project_settings: dict,
        old_data: Optional[dict] = None,
        old_settings: Optional[dict] = None,
        request: Optional[HttpRequest] = None,
    ):
        """
        Revert project creation or update if errors have occurred in other apps.

        :param project: Current project object (Project)
        :param action: Action which was performed (CREATE or UPDATE)
        :param project_settings: Project app settings (dict)
        :param old_data: Old project data in case of update (dict or None)
        :param old_settings: Old app settings in case of update (dict or None)
        :param request: Request object or None
        """
        pass

    def perform_role_modify(
        self,
        role_as: RoleAssignment,
        action: str,
        old_role: Optional[Role] = None,
        request: Optional[HttpRequest] = None,
    ):
        """
        Perform additional actions to finalize role assignment creation or
        update.

        :param role_as: RoleAssignment object
        :param action: Action to perform (CREATE or UPDATE)
        :param old_role: Role object for previous role in case of an update
        :param request: Request object or None
        """
        pass

    def revert_role_modify(
        self,
        role_as: RoleAssignment,
        action: str,
        old_role: Optional[Role] = None,
        request: Optional[HttpRequest] = None,
    ):
        """
        Revert role assignment creation or update if errors have occurred in
        other apps.

        :param role_as: RoleAssignment object
        :param action: Action which was performed (CREATE or UPDATE)
        :param old_role: Role object for previous role in case of an update
        :param request: Request object or None
        """
        pass

    def perform_role_delete(
        self,
        role_as: RoleAssignment,
        request: Optional[HttpRequest] = None,
    ):
        """
        Perform additional actions to finalize role assignment deletion.

        :param role_as: RoleAssignment object
        :param request: Request object or None
        """
        pass

    def revert_role_delete(
        self,
        role_as: RoleAssignment,
        request: Optional[HttpRequest] = None,
    ):
        """
        Revert role assignment deletion deletion if errors have occurred in
        other apps.

        :param role_as: RoleAssignment object
        :param request: Request object or None
        """
        pass

    def perform_owner_transfer(
        self,
        project: Project,
        new_owner: SODARUser,
        old_owner: SODARUser,
        old_owner_role: Optional[Role] = None,
        request: Optional[HttpRequest] = None,
    ):
        """
        Perform additional actions to finalize project ownership transfer.

        :param project: Project object
        :param new_owner: SODARUser object for new owner
        :param old_owner: SODARUser object for previous owner
        :param old_owner_role: Role object for new role of old owner or None
        :param request: Request object or None
        """
        pass

    def revert_owner_transfer(
        self,
        project: Project,
        new_owner: SODARUser,
        old_owner: SODARUser,
        old_owner_role: Optional[Role] = None,
        request: Optional[HttpRequest] = None,
    ):
        """
        Revert project ownership transfer if errors have occurred in other apps.

        :param project: Project object
        :param new_owner: SODARUser object for new owner
        :param old_owner: SODARUser object for previous owner
        :param old_owner_role: Role object for new role of old owner or None
        :param request: Request object or None
        """
        pass

    def perform_project_sync(self, project: Project):
        """
        Synchronize existing projects to ensure related data exists when the
        syncmodifyapi management comment is called. Should mostly be used in
        development when the development databases have been e.g. modified or
        recreated.

        :param project: Current project object (Project)
        """
        pass

    def perform_project_setting_update(
        self,
        plugin_name: str,
        setting_name: str,
        value: Any,
        old_value: Any,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Perform additional actions when updating a single app setting with
        PROJECT scope.

        :param plugin_name: Name of app plugin for the setting, "projectroles"
                            is used for projectroles settings (string)
        :param setting_name: Setting name (string)
        :param value: New value for setting
        :param old_value: Previous value for setting
        :param project: Project object or None
        :param user: User object or None
        """
        pass

    def revert_project_setting_update(
        self,
        plugin_name: str,
        setting_name: str,
        value: Any,
        old_value: Any,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Revert updating a single app setting with PROJECT scope if errors have
        occurred in other apps.

        :param plugin_name: Name of app plugin for the setting, "projectroles"
                            is used for projectroles settings (string)
        :param setting_name: Setting name (string)
        :param value: New value for setting
        :param old_value: Previous value for setting
        :param project: Project object or None
        :param user: User object or None
        """
        pass

    def perform_project_archive(self, project: Project):
        """
        Perform additional actions to finalize project archiving or unarchiving.
        The state being applied can be derived from the project.archive attr.

        :param project: Project object (Project)
        """
        pass

    def revert_project_archive(self, project: Project):
        """
        Revert project archiving or unarchiving if errors have occurred in other
        apps. The state being originally set can be derived from the
        project.archive attr.

        :param project: Project object (Project)
        """
        pass

    def perform_project_delete(self, project: Project):
        """
        Perform additional actions to finalize project deletion.

        NOTE: This operation can not be undone so there is no revert method.

        :param project: Project object (Project)
        """
        pass


# Plugin Points ----------------------------------------------------------------


class ProjectAppPluginPoint(PluginPoint):
    """Projectroles plugin point for registering project specific apps"""

    #: UI URLs
    urls = []

    #: App setting definitions
    #:
    #: Example ::
    #:
    #:     app_settings = [
    #:         PluginAppSettingDef(
    #:             name='example_setting',  # Must be unique within plugin
    #:             scope=APP_SETTING_SCOPE_PROJECT,
    #:             type=APP_SETTING_TYPE_STRING,
    #:             default='example',  # Optional
    #:             label='Example setting',  # Optional
    #:             placeholder='Enter example setting here',  # Optional
    #:             description='Example user setting',  # Optional
    #:             options=['example', 'example2'],  # Optional, only for STRING
    #:                                               # or INTEGER settings
    #:             user_modifiable=True,  # Optional, show/hide in forms
    #:             global_edit=False,  # Optional, enable/disable editing on
    #:                                 # target sites
    #:             widget_attrs={},  # Optional, widget attrs for forms
    #:         )
    #:    ]
    app_settings = []

    # DEPRECATED, will be removed in the next SODAR Core release
    project_settings = {}

    #: Iconify icon
    icon = 'mdi:help-rhombus-outline'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'home'

    #: Description string
    description = 'TODO: Write a description for your plugin'

    #: Required permission for accessing the app
    app_permission = None

    #: Enable or disable general search from project title bar
    search_enable = False

    #: List of search object types for the app
    search_types = []

    #: Search results template
    search_template = None

    #: App card template for the project details page
    details_template = None

    #: App card title for the project details page
    details_title = None

    #: Position in plugin ordering
    plugin_ordering = 50

    #: Optional custom project list column definition
    #:
    #: Example ::
    #:
    #:     project_list_columns = {
    #:         'column_id': {
    #:             'title': 'Column Title',
    #:             'width': 100,  # Desired width of column in pixels
    #:             'description': 'Description',  # Optional description string
    #:             'active': True,  # Boolean for whether the column is active
    #:             'ordering': 50,  # Integer for ordering the columns
    #:             'align': 'left'  # Alignment of content
    #:         }
    #:     }
    project_list_columns = {}

    #: Display application for categories in addition to projects
    category_enable = False

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = []

    def get_object(
        self, model: type[Model], uuid: Union[str, UUID]
    ) -> Optional[Model]:
        """
        Return object based on a model class and the object's SODAR UUID.

        :param model: Object model class
        :param uuid: sodar_uuid of the referred object
        :return: Model object or None if not found
        :raise: NameError if model is not found
        """
        try:
            return model.objects.get(sodar_uuid=uuid)
        except model.DoesNotExist:
            return None

    def get_object_link(
        self, model_str: str, uuid: Union[str, UUID]
    ) -> Optional['PluginObjectLink']:
        """
        Return URL referring to an object used by the app, along with a name to
        be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: PluginObjectLink or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)
        if not obj:
            return None
        return None

    def get_extra_data_link(
        self, _extra_data: dict, _name: str
    ) -> Optional[str]:
        """Return a link for timeline label starting with 'extra-'"""
        return None

    def search(
        self,
        search_terms: list[str],
        user: SODARUser,
        search_type: Optional[str] = None,
        keywords: Optional[list[str]] = None,
    ) -> list['PluginSearchResult']:
        """
        Return app items based on one or more search terms, user, optional type
        and optional keywords.

        :param search_terms: Search terms to be joined with the OR operator
                             (list of strings)
        :param user: User object for user initiating the search
        :param search_type: String
        :param keywords: List (optional)
        :return: List of PluginSearchResult objects
        """
        # TODO: If implemented, also implement display of results in the app's
        #       search template
        return []

    def update_cache(
        self,
        name: Optional[str] = None,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ):
        """
        Update cached data for this app, limitable to item ID and/or project.

        :param name: Item name to limit update to (string, optional)
        :param project: Project object to limit update to (optional)
        :param user: User object to denote user triggering the update (optional)
        """
        return None

    def get_statistics(self) -> dict:
        """
        Return app statistics as a dict. Should take the form of
        {id: {label, value, url (optional), description (optional)}}.

        :return: Dict
        """
        return {}

    def get_category_stats(
        self, category: Project
    ) -> list['PluginCategoryStatistic']:
        """
        Return app statistics for the given category. Expected to return
        cumulative statistics for all projects under the category and its
        possible subcategories.

        :param category: Project object of CATEGORY type
        :return: List of PluginCategoryStatistic objects
        """
        return []

    def get_project_list_value(
        self, column_id: str, project: Project, user: SODARUser
    ) -> Union[str, int, None]:
        """
        Return a value for the optional additional project list column specific
        to a project.

        :param column_id: ID of the column (string)
        :param project: Project object
        :param user: User object (current user)
        :return: String (may contain HTML), integer or None
        """
        return None

    def validate_form_app_settings(
        self,
        app_settings: dict,
        project: Optional[Project] = None,
        user: Optional[SODARUser] = None,
    ) -> Optional[dict]:
        """
        Validate app settings form data and return a dict of errors.

        :param app_settings: Dict of app settings
        :param project: Project object or None
        :param user: User object or None
        :return: dict in format of {setting_name: 'Error string'}
        """
        return None


class BackendPluginPoint(PluginPoint):
    """Projectroles plugin point for registering backend apps"""

    #: Iconify icon
    icon = 'mdi:help-rhombus-outline'

    #: Description string
    description = 'TODO: Write a description for your plugin'

    #: URL of optional javascript file to be included
    javascript_url = None

    #: URL of optional css file to be included
    css_url = None

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = []

    def get_api(self) -> Any:
        """Return API entry point object"""
        raise NotImplementedError

    def get_statistics(self) -> dict:
        """
        Return backend statistics as a dict. Should take the form of
        {id: {label, value, url (optional), description (optional)}}.

        :return: Dict
        """
        return {}

    def get_object(
        self, model: type[Model], uuid: Union[str, UUID]
    ) -> Optional[Model]:
        """
        Return object based on a model class and the object's SODAR UUID.

        :param model: Object model class
        :param uuid: sodar_uuid of the referred object
        :return: Model object or None if not found
        :raise: NameError if model is not found
        """
        try:
            return model.objects.get(sodar_uuid=uuid)
        except model.DoesNotExist:
            return None

    def get_object_link(
        self, model_str: str, uuid: Union[str, UUID]
    ) -> Optional['PluginObjectLink']:
        """
        Return URL referring to an object used by the app, along with a name to
        be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: PluginObjectLink or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)
        if not obj:
            return None
        return None

    def get_extra_data_link(
        self, _extra_data: dict, _name: str
    ) -> Optional[str]:
        """Return a link for timeline label starting with 'extra-'"""
        return None


class SiteAppPluginPoint(PluginPoint):
    """Projectroles plugin point for registering site-wide apps"""

    #: Iconify icon
    icon = 'mdi:help-rhombus-outline'

    #: Description string
    description = 'TODO: Write a description for your plugin'

    #: Entry point URL ID
    entry_point_url_id = 'home'

    #: Required permission for displaying the app
    app_permission = None

    #: User settings definition
    #:
    #: Example ::
    #:
    #:     app_settings = [
    #:         PluginAppSettingDef(
    #:             name='example_setting',  # Must be unique within plugin
    #:             scope=APP_SETTING_SCOPE_USER,  # Use USER or SITE
    #:             type=APP_SETTING_TYPE_STRING,
    #:             default='example',  # Optional
    #:             label='Example setting',  # Optional
    #:             placeholder='Enter example setting here',  # Optional
    #:             description='Example user setting',  # Optional
    #:             options=['example', 'example2'],  # Optional, only for STRING
    #:                                               # or INTEGER settings
    #:             user_modifiable=True,  # Optional, show/hide in forms
    #:             global_edit=False,  # Optional, enable/disable editing on
    #:                                 # target sites
    #:             widget_attrs={},  # Optional, widget attrs for forms
    #:         )
    #:    ]
    app_settings = []

    #: List of names for plugin specific Django settings to display in siteinfo
    info_settings = []

    def get_statistics(self) -> dict:
        """
        Return app statistics as a dict. Should take the form of
        {id: {label, value, url (optional), description (optional)}}.

        :return: Dict
        """
        return {}

    def get_messages(self, user: Optional[SODARUser] = None) -> list[dict]:
        """
        Return a list of messages to be shown to users.

        :param user: User object (optional)
        :return: List of dicts or and empty list if no messages
        """
        '''
        Example of valid return data:
        return [{
            'content': 'Message content in here, can contain html',
            'color': 'info',        # Corresponds to bg-* in Bootstrap
            'dismissable': True     # False for non-dismissable
        }]
        '''
        return []

    def get_object(
        self, model: type[Model], uuid: Union[str, UUID]
    ) -> Optional[Model]:
        """
        Return object based on a model class and the object's SODAR UUID.

        :param model: Object model class
        :param uuid: sodar_uuid of the referred object
        :return: Model object or None if not found
        :raise: NameError if model is not found
        """
        try:
            return model.objects.get(sodar_uuid=uuid)
        except model.DoesNotExist:
            return None

    def get_object_link(
        self, model_str: str, uuid: Union[str, UUID]
    ) -> Optional['PluginObjectLink']:
        """
        Return URL referring to an object used by the app, along with a name to
        be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: PluginObjectLink or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)
        if not obj:
            return None
        return None

    def get_extra_data_link(
        self, _extra_data: dict, _name: str
    ) -> Optional[str]:
        """Return a link for timeline label starting with 'extra-'"""
        return None

    def validate_form_app_settings(
        self,
        app_settings: dict,
        user: Optional[SODARUser] = None,
    ) -> Optional[dict]:
        """
        Validate app settings form data and return a dict of errors.

        :param app_settings: Dict of app settings
        :param user: User object or None
        :return: dict in format of {setting_name: 'Error string'}
        """
        return None


# Data Classes -----------------------------------------------------------------


class PluginAppSettingDef:
    """
    Class representing an AppSetting definition. Expected to be used to define
    app settings in the plugin app_settings variable.
    """

    def __init__(
        self,
        name: str,
        scope: str,
        type: str,
        default: Optional[Any] = None,
        label: Optional[str] = None,
        placeholder: Union[str, int, None] = None,
        description: Optional[str] = None,
        options: Union[callable, list, None] = None,
        user_modifiable: Optional[
            bool
        ] = None,  # Set None here to validate PROJECT_USER value
        global_edit: bool = False,
        project_types: Optional[list[str]] = None,
        widget_attrs: Optional[dict] = None,
    ):
        """
        Initialize PluginAppSettingDef.

        :param name: Setting name to be used internally (string)
        :param scope: Setting scope, must correspond to one of
                      APP_SETTING_SCOPE_* (string)
        :param type: Setting type, must correspond to one of APP_SETTING_TYPE_*
                     (string)
        :param default: Default value, type depends on setting type. Can be a
                        callable.
        :param label: Display label (string, optional, name is used as default)
        :param placeholder: Placeholder value to be displayed in forms (string,
                            optional)
        :param description: Detailed setting description (string, optional)
        :param options: Limit value to given options. Can be callable (optional,
                        only for STRING or INTEGER types)
        :param user_modifiable: Display in forms for user if True (optional,
                                default=True, only for PROJECT and USER scopes)
        :param global_edit: Only allow editing on source site if True (optional,
                            default=False)
        :param project_types: Allowed project types (optional,
                              default=[PROJECT_TYPE_PROJECT])
        :parm widget_attrs: Form widget attributes (optional, dict)
        :raise: ValueError if an argument is not valid
        """
        # Validate provided values
        self.validate_scope(scope)
        self.validate_type(type)
        self.validate_type_options(type, options)
        if not callable(default):
            self.validate_value(type, default)
        if (
            default is not None
            and options is not None
            and not callable(default)
            and not callable(options)
        ):
            self.validate_default_in_options(default, options)
        # Validate and set user_modifiable
        self.validate_user_modifiable(scope, user_modifiable)
        if user_modifiable is None:
            user_modifiable = (
                False if scope == APP_SETTING_SCOPE_PROJECT_USER else True
            )
        # Set members
        self.name = name
        self.scope = scope
        self.type = type
        self.default = (
            ''
            if type == APP_SETTING_TYPE_STRING and default is None
            else default
        )
        self.label = label
        self.placeholder = placeholder
        self.description = description
        self.options = options or []
        self.user_modifiable = user_modifiable
        self.global_edit = global_edit
        self.project_types = project_types or [PROJECT_TYPE_PROJECT]
        self.widget_attrs = widget_attrs or {}

    @classmethod
    def validate_scope(cls, scope: str):
        """
        Validate the app setting scope.

        :param scope: String
        :raise: ValueError if scope is not recognized
        """
        if scope not in APP_SETTING_SCOPES:
            raise ValueError(f'Invalid scope "{scope}"')

    @classmethod
    def validate_type(cls, setting_type: str):
        """
        Validate the app setting type.

        :param setting_type: String
        :raise: ValueError if type is not recognized
        """
        if setting_type not in APP_SETTING_TYPES:
            raise ValueError(f'Invalid setting type "{setting_type}"')

    @classmethod
    def validate_type_options(cls, setting_type: str, setting_options: list):
        """
        Validate existence of options against setting type.

        :param setting_type: String
        :param setting_options: List of options (Strings or Integers)
        :raise: ValueError if type is not recognized
        """
        if (
            setting_type
            not in [APP_SETTING_TYPE_INTEGER, APP_SETTING_TYPE_STRING]
            and setting_options
        ):
            raise ValueError(
                'Options are only allowed for settings of type INTEGER and '
                'STRING'
            )

    @classmethod
    def validate_default_in_options(
        cls, setting_default: Any, setting_options: Any
    ):
        """
        Validate existence of default value in uncallable options.

        :param setting_default: Default value
        :param setting_options: Setting options
        :raise: ValueError if default is not found in options
        """
        opts = [o[0] if isinstance(o, tuple) else o for o in setting_options]
        if (
            setting_options is not None
            and not callable(setting_options)
            and setting_default is not None
            and not callable(setting_default)
            and setting_default not in opts
        ):
            raise ValueError(
                'Default value "{}" not found in options ({})'.format(
                    setting_default,
                    ', '.join([str(o) for o in opts]),
                )
            )

    @classmethod
    def validate_value(cls, setting_type: str, setting_value: Any):
        """
        Validate non-callable value.

        :param setting_type: Setting type (string)
        :param setting_value: Setting value
        :raise: ValueError if value is invalid
        """
        if setting_type == APP_SETTING_TYPE_BOOLEAN:
            if not isinstance(setting_value, bool):
                raise ValueError(
                    f'Please enter value as bool (value={setting_value}; '
                    f'type={type(setting_value)})'
                )
        elif setting_type == APP_SETTING_TYPE_INTEGER:
            if (
                not isinstance(setting_value, int)
                and not str(setting_value).isdigit()
            ):
                raise ValueError(
                    f'Please enter a valid integer value ({setting_value})'
                )
        elif setting_type == APP_SETTING_TYPE_JSON:
            if setting_value and not isinstance(setting_value, (dict, list)):
                raise ValueError(
                    f'Please enter JSON value as dict or list '
                    f'(value={setting_value}; type={type(setting_value)})'
                )
            try:
                json.dumps(setting_value)
            except TypeError:
                raise ValueError(f'Please enter valid JSON ({setting_value})')

    @classmethod
    def validate_user_modifiable(
        cls, scope: str, user_modifiable: Optional[bool]
    ):
        """
        Validate user_modifiable against scope.

        :param scope: String
        :param user_modifiable: Bool or None
        :raises: ValueError if user_modifiable can't be set for scope
        """
        if user_modifiable and scope == APP_SETTING_SCOPE_PROJECT_USER:
            raise ValueError(
                'Argument user_modifiable can not be set True for PROJECT_USER '
                'scope settings'
            )


class PluginObjectLink:
    """
    Class representing a hyperlink to an object used by the app. Expected to be
    returned from get_object_link() implementations.
    """

    #: URL to the object (string)
    url = None
    #: Name of the object to be displayed in link (string, formerly "label")
    name = None
    #: Open the link in a blank browser tab (boolean, default=False)
    blank = False

    def __init__(self, url: str, name: str, blank: bool = False):
        """
        Initialize PluginObjectLink.

        :param url: URL to the object (string)
        :param name: Name of the object to be displayed in link (string,
                     formerly "label")
        :param blank: Open the link in a blank browser tab (boolean,
                      default=False)
        """
        self.url = url
        self.name = name
        self.blank = blank


class PluginSearchResult:
    """
    Class representing a list of search results from a specific plugin for one
    or more search types. Expected to be returned from search() implementations.
    """

    #: Category of the result set, used in templates (string)
    category = None
    #: Title to be displayed for this set of search results in the UI (string)
    title = None
    #: List of one or more search type keywords for these results
    search_types = []
    #: List or QuerySet of result objects
    items = []

    def __init__(
        self,
        category: str,
        title: str,
        search_types: Optional[list[str]],
        items: Union[list, QuerySet],
    ):
        """
        Initialize PluginSearchResult.

        :param category: Category of the result set, used in templates (string)
        :param title: Title to be displayed for this set of search results in
                      the UI (string)
        :param search_types: List of one or more search type keywords for the
                             results
        :param items: List or QuerySet of result objects
        """
        self.category = category
        self.title = title
        self.search_types = search_types
        if not isinstance(search_types, list) or len(search_types) < 1:
            raise ValueError(
                'At least one type keyword must be provided in search_types'
            )
        self.items = items


class PluginCategoryStatistic:
    """Class representing an item of category statistics"""

    #: Plugin from which this item is initialized (None for projectroles)
    plugin = None
    #: Title to be displayed (string)
    title = None
    #: Value of the statistic (int or float)
    value = 0
    #: Optional unit (string or None)
    unit = None
    #: Optional description to be displayed as tooltip (string or None)
    description = None
    #: Optional icon namespace and ID (string or None)

    def __init__(
        self,
        plugin: Optional[ProjectAppPluginPoint],
        title: str,
        value: Union[int, float],
        unit: Optional[str] = None,
        description: Optional[str] = None,
        icon: Optional[str] = None,
    ):
        """
        Initialize PluginCategoryStatistic.

        :param plugin: ProjectAppPluginPoint object (None for projectroles)
        :param title: String
        :param value: Integer or float
        :param unit: String or None
        :param description: String or None
        :param icon: String or None
        :raises: ValueError if value is not integer or float
        """
        self.plugin = plugin
        self.title = title
        if not isinstance(value, int) and not isinstance(value, float):
            raise ValueError('Value must be integer or float')
        self.value = value
        self.unit = unit
        self.description = description
        if icon:
            self.icon = icon
        elif plugin:
            self.icon = getattr(plugin, 'icon')


# Plugin API -------------------------------------------------------------------


class PluginAPI:
    """API for SODAR Core plugin retrieval"""

    @classmethod
    def get_active_plugins(
        cls, plugin_type: str = 'project_app', custom_order: bool = False
    ) -> Optional[list[PluginPoint]]:
        """
        Return active plugins of a specific type.

        :param plugin_type: "project_app", "site_app" or "backend" (string)
        :param custom_order: Order by plugin_ordering for project apps (boolean)
        :return: List or None
        :raise: ValueError if plugin_type is not recognized
        """
        if plugin_type not in PLUGIN_TYPES.keys():
            raise ValueError(
                'Invalid value for plugin_type. Accepted values: {}'.format(
                    ', '.join(PLUGIN_TYPES.keys())
                )
            )
        plugins = eval(PLUGIN_TYPES[plugin_type]).get_plugins()
        if plugins:
            ret = [
                p
                for p in plugins
                if (
                    p.is_active()
                    and (
                        plugin_type in ['project_app', 'site_app']
                        or p.name in settings.ENABLED_BACKEND_PLUGINS
                    )
                )
            ]
            return sorted(
                ret,
                key=lambda x: (
                    x.plugin_ordering
                    if custom_order and plugin_type == 'project_app'
                    else x.name
                ),
            )
        return None

    @classmethod
    def change_plugin_status(
        cls, name: str, status: int, plugin_type: str = 'app'
    ):
        """
        Change the status of a selected plugin in the database.

        :param name: Plugin name (string)
        :param status: Status (int, see djangoplugins)
        :param plugin_type: Type of plugin ("app", "backend" or "site")
        :raise: ValueError if plugin_type is invalid or plugin with name not
                found
        """
        # NOTE: Used to forge plugin to a specific status for e.g. testing
        if plugin_type == 'app':
            plugin = ProjectAppPluginPoint.get_plugin(name)
        elif plugin_type == 'backend':
            plugin = BackendPluginPoint.get_plugin(name)
        elif plugin_type == 'site':
            plugin = SiteAppPluginPoint.get_plugin(name)
        else:
            raise ValueError(f'Invalid plugin_type: "{plugin_type}"')
        if not plugin:
            raise ValueError(
                f'Plugin of type "{plugin_type}" not found with name "{name}"'
            )
        plugin = plugin.get_model()
        plugin.status = status
        plugin.save()

    @classmethod
    def get_app_plugin(
        cls, plugin_name: str, plugin_type: Optional[str] = None
    ) -> Optional[PluginPoint]:
        """
        Return active app plugin.

        :param plugin_name: Plugin name (string)
        :param plugin_type: Plugin type (string or None for all types)
        :return: Plugin object or None if not found or inactive
        """
        if plugin_type:
            plugin_types = [PLUGIN_TYPES[plugin_type]]
        else:
            plugin_types = PLUGIN_TYPES.values()
        for t in plugin_types:
            try:
                return eval(t).get_plugin(plugin_name)
            except Exception:
                pass
        return None

    @classmethod
    def get_backend_api(
        cls, plugin_name: str, force: bool = False, **kwargs
    ) -> Optional[BackendPluginPoint]:
        """
        Return backend API object.
        NOTE: May raise an exception from plugin.get_api().

        :param plugin_name: Plugin name (string)
        :param force: Return plugin regardless of status in
                      ENABLED_BACKEND_PLUGINS
        :param kwargs: Optional kwargs for API
        :return: Plugin object or None if not found
        """
        if plugin_name in settings.ENABLED_BACKEND_PLUGINS or force:
            try:
                plugin = BackendPluginPoint.get_plugin(plugin_name)
            except BackendPluginPoint.DoesNotExist:
                return None
            return plugin.get_api(**kwargs) if plugin.is_active() else None
        return None


# TODO: Remove in v1.3 (see #1718)
def get_active_plugins(
    plugin_type: str = 'project_app', custom_order: bool = False
) -> Optional[list[PluginPoint]]:
    """
    Return active plugins of a specific type.

    DEPRECATED: To be removed in v1.3. Use method in PluginAPI instead.

    :param plugin_type: "project_app", "site_app" or "backend" (string)
    :param custom_order: Order by plugin_ordering for project apps (boolean)
    :return: List or None
    :raise: ValueError if plugin_type is not recognized
    """
    logger.warning(PLUGIN_API_DEPRECATE_MSG.format(method='get_active_plugins'))
    plugin_api = PluginAPI()
    return plugin_api.get_active_plugins(plugin_type, custom_order)


# TODO: Remove in v1.3 (see #1718)
def change_plugin_status(name: str, status: int, plugin_type: str = 'app'):
    """
    Change the status of a selected plugin in the database.

    DEPRECATED: To be removed in v1.3. Use method in PluginAPI instead.

    :param name: Plugin name (string)
    :param status: Status (int, see djangoplugins)
    :param plugin_type: Type of plugin ("app", "backend" or "site")
    :raise: ValueError if plugin_type is invalid or plugin with name not found
    """
    # NOTE: Used to forge plugin to a specific status for e.g. testing
    logger.warning(
        PLUGIN_API_DEPRECATE_MSG.format(method='change_plugin_status')
    )
    plugin_api = PluginAPI()
    plugin_api.change_plugin_status(name, status, plugin_type)


# TODO: Remove in v1.3 (see #1718)
def get_app_plugin(
    plugin_name: str, plugin_type: Optional[str] = None
) -> Optional[PluginPoint]:
    """
    Return active app plugin.

    DEPRECATED: To be removed in v1.3. Use method in PluginAPI instead.

    :param plugin_name: Plugin name (string)
    :param plugin_type: Plugin type (string or None for all types)
    :return: Plugin object or None if not found or inactive
    """
    logger.warning(PLUGIN_API_DEPRECATE_MSG.format(method='get_app_plugin'))
    plugin_api = PluginAPI()
    return plugin_api.get_app_plugin(plugin_name, plugin_type)


# TODO: Remove in v1.3 (see #1718)
def get_backend_api(
    plugin_name: str, force: bool = False, **kwargs
) -> Optional[BackendPluginPoint]:
    """
    Return backend API object.
    NOTE: May raise an exception from plugin.get_api().

    DEPRECATED: To be removed in v1.3. Use method in PluginAPI instead.

    :param plugin_name: Plugin name (string)
    :param force: Return plugin regardless of status in ENABLED_BACKEND_PLUGINS
    :param kwargs: Optional kwargs for API
    :return: Plugin object or None if not found
    """
    logger.warning(PLUGIN_API_DEPRECATE_MSG.format(method='get_backend_api'))
    plugin_api = PluginAPI()
    return plugin_api.get_backend_api(plugin_name, force, **kwargs)


# Plugins within projectroles --------------------------------------------------


class RemoteSiteAppPlugin(SiteAppPluginPoint):
    """Site plugin for remote site and project management"""

    #: Name (used as plugin ID)
    name = 'remotesites'

    #: Title (used in templates)
    title = 'Remote Site Access'

    #: UI URLs
    urls = []

    #: Iconify icon
    icon = 'mdi:cloud-sync'

    #: Description string
    description = 'Management of remote SODAR sites and remote project access'

    #: Entry point URL ID
    entry_point_url_id = 'projectroles:remote_sites'

    #: Required permission for displaying the app
    app_permission = 'projectroles.update_remote'


class SiteAppSettingsAppPlugin(SiteAppPluginPoint):
    """Site plugin for site app settings"""

    #: Name (used as plugin ID)
    name = 'siteappsettings'

    #: Title (used in templates)
    title = 'Site App Settings'

    #: UI URLs
    urls = []

    #: Iconify icon
    icon = 'mdi:cog-outline'

    #: Description string
    description = 'Site-wide app setting management'

    #: Entry point URL ID
    entry_point_url_id = 'projectroles:site_app_settings'

    #: Required permission for displaying the app
    app_permission = 'projectroles.update_site_settings'
