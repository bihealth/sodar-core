"""Plugins for the example_project_app Django app"""

from django.contrib import messages
from django.urls import reverse

# Projectroles dependency
from projectroles.app_settings import (
    get_example_setting_default,
    get_example_setting_options,
)
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import (
    ProjectAppPluginPoint,
    ProjectModifyPluginMixin,
)
from projectroles.utils import get_display_name

from example_project_app.urls import urlpatterns


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']

# Local constants
EXAMPLE_MODIFY_API_MSG = (
    'Example project app plugin API called from {project_type} {action}.'
)
# Invalid app setting value for testing custom validation
INVALID_SETTING_VALUE = 'ieDeequ6Eizohxi7Eebiliu6shou5aiT'
INVALID_SETTING_MSG = 'INVALID_SETTING_VALUE detected'


class ProjectAppPlugin(ProjectModifyPluginMixin, ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (slug-safe)
    name = 'example_project_app'

    #: Title (used in templates)
    title = 'Example Project App'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: Project and user settings
    # TODO: Unify naming
    app_settings = {
        'project_str_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'String setting',
            'default': '',
            'description': 'Example string project setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        },
        'project_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'INTEGER',
            'label': 'Integer setting',
            'default': 0,
            'description': 'Example integer project setting',
            'user_modifiable': True,
            'placeholder': 0,
            'widget_attrs': {'class': 'text-success'},
        },
        'project_str_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'String setting with options',
            'default': 'string1',
            'description': 'Example string project setting with options',
            'options': ['string1', 'string2'],
            'user_modifiable': True,
        },
        'project_int_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'INTEGER',
            'label': 'Integer setting with options',
            'default': 0,
            'description': 'Example integer project setting with options',
            'options': [0, 1],
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-success'},
        },
        'project_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'BOOLEAN',
            'label': 'Boolean setting',
            'default': False,
            'description': 'Example boolean project setting',
            'user_modifiable': True,
        },
        'project_global_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'BOOLEAN',
            'label': 'Global boolean setting',
            'default': False,
            'description': 'Example global boolean project setting',
            'user_modifiable': True,
            'local': False,
        },
        'project_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'JSON',
            'label': 'JSON setting',
            'default': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'description': 'Example JSON project setting',
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-danger'},
        },
        'project_hidden_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'Hidden setting',
            'default': '',
            'description': 'Example hidden project setting',
            'user_modifiable': False,
        },
        'project_hidden_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'JSON',
            'label': 'Hidden JSON setting',
            'description': 'Example hidden JSON project setting',
            'user_modifiable': False,
        },
        'user_str_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'String setting',
            'default': '',
            'description': 'Example string user setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        },
        'user_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'INTEGER',
            'label': 'Integer setting',
            'default': 0,
            'description': 'Example integer user setting',
            'placeholder': 0,
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-success'},
        },
        'user_str_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'String setting with options',
            'default': 'string1',
            'options': ['string1', 'string2'],
            'description': 'Example string user setting with options',
            'user_modifiable': True,
        },
        'user_int_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'INTEGER',
            'label': 'Integer setting with options',
            'default': 0,
            'options': [0, 1],
            'description': 'Example integer user setting with options',
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-success'},
        },
        'user_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'BOOLEAN',
            'label': 'Boolean setting',
            'default': False,
            'description': 'Example boolean user setting',
            'user_modifiable': True,
        },
        'user_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'JSON',
            'label': 'JSON setting',
            'default': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'description': 'Example JSON user setting',
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-danger'},
        },
        'user_hidden_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'default': '',
            'description': 'Example hidden user setting',
            'user_modifiable': False,
        },
        'project_user_str_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'STRING',
            'default': '',
            'description': 'Example string project user setting',
        },
        'project_user_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'INTEGER',
            'default': 0,
            'description': 'Example int project user setting',
        },
        'project_user_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'BOOLEAN',
            'default': False,
            'description': 'Example bool project user setting',
        },
        'project_user_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'JSON',
            'default': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'description': 'Example json project user setting',
        },
        'project_callable_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'Callable project setting',
            'default': get_example_setting_default,
            'description': 'Example callable project setting',
        },
        'user_callable_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'Callable user setting',
            'default': get_example_setting_default,
            'description': 'Example callable user setting',
        },
        'project_user_callable_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'STRING',
            'default': get_example_setting_default,
            'description': 'Example callable project user setting',
        },
        'project_callable_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'Callable setting with options',
            'default': get_example_setting_default,
            'options': get_example_setting_options,
            'description': 'Example callable project setting with options',
            'user_modifiable': True,
        },
        'user_callable_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'Callable setting with options',
            'default': get_example_setting_default,
            'options': get_example_setting_options,
            'description': 'Example callable user setting with options',
            'user_modifiable': True,
        },
        'project_user_callable_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'STRING',
            'default': get_example_setting_default,
            'options': get_example_setting_options,
            'description': 'Example callable project user setting with options',
        },
        'project_category_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'BOOLEAN',
            'label': 'Category boolean setting',
            'default': False,
            'description': 'Example boolean project category setting',
            'user_modifiable': True,
            'project_types': [PROJECT_TYPE_CATEGORY],
        },
        'site_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_SITE'],
            'type': 'BOOLEAN',
            'label': 'Site boolean setting',
            'default': False,
            'description': 'Example boolean site setting',
            'user_modifiable': True,
        },
    }

    #: Iconify icon
    icon = 'mdi:rocket-launch'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'example_project_app:example'

    #: Description string
    description = 'This is a minimal example for a project app'

    #: Required permission for accessing the app
    app_permission = 'example_project_app.view_data'

    #: Enable or disable general search from project title bar
    search_enable = False

    #: List of search object types for the app
    search_types = []

    #: Search results template
    search_template = None

    #: App card template for the project details page
    details_template = 'example_project_app/_details_card.html'

    #: App card title for the project details page
    details_title = 'Example Project App Overview'

    #: Position in plugin ordering
    plugin_ordering = 100

    def get_statistics(self):
        return {
            'example_stat': {
                'label': 'Example Stat',
                'value': 9000,
                'description': 'Optional description goes here',
            },
            'second_example': {
                'label': 'Second Example w/ Link',
                'value': 56000,
                'url': reverse('home'),
            },
        }

    def perform_project_modify(
        self,
        project,
        action,
        project_settings,
        old_data=None,
        old_settings=None,
        request=None,
    ):
        """Example implementation for project modifying plugin API"""
        if request:
            messages.info(
                request,
                EXAMPLE_MODIFY_API_MSG.format(
                    project_type=get_display_name(project.type),
                    action=action.lower(),
                ),
            )

    def validate_form_app_settings(self, app_settings, project=None, user=None):
        """Example implementation for custom form app setting validation"""
        ret = {}
        if (
            project
            and app_settings.get('project_str_setting') == INVALID_SETTING_VALUE
        ):
            ret['project_str_setting'] = INVALID_SETTING_MSG
        if (
            user
            and app_settings.get('user_str_setting') == INVALID_SETTING_VALUE
        ):
            ret['user_str_setting'] = INVALID_SETTING_MSG
        return ret
