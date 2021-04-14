from django.conf import settings
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import ProjectAppPluginPoint

from example_project_app.urls import urlpatterns


class ProjectAppPlugin(ProjectAppPluginPoint):
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
    app_settings = {
        'project_str_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'String Setting',
            'default': '',
            'description': 'Example string project setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        },
        'project_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'INTEGER',
            'label': 'Integer Setting',
            'default': 0,
            'description': 'Example integer project setting',
            'user_modifiable': True,
            'placeholder': 0,
            'widget_attrs': {'class': 'text-success'},
        },
        'project_str_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'STRING',
            'label': 'String Setting',
            'default': 'string1',
            'description': 'Example string project setting with options',
            'options': ['string1', 'string2'],
            'user_modifiable': True,
        },
        'project_int_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'INTEGER',
            'label': 'Integer Setting',
            'default': 0,
            'description': 'Example integer project setting with options',
            'options': [0, 1],
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-success'},
        },
        'project_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'BOOLEAN',
            'label': 'Boolean Setting',
            'default': False,
            'description': 'Example boolean project setting',
            'user_modifiable': True,
        },
        'project_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'JSON',
            'label': 'JSON Setting',
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
            'default': '',
            'description': 'Example hidden project setting',
            'user_modifiable': False,
        },
        'project_hidden_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT'],
            'type': 'JSON',
            'description': 'Example hidden JSON project setting',
            'user_modifiable': False,
        },
        'user_str_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'String Setting',
            'default': '',
            'description': 'Example string user setting',
            'placeholder': 'Example string',
            'user_modifiable': True,
        },
        'user_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'INTEGER',
            'label': 'Integer Setting',
            'default': 0,
            'description': 'Example integer user setting',
            'placeholder': 0,
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-success'},
        },
        'user_str_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'STRING',
            'label': 'String Setting',
            'default': 'string1',
            'options': ['string1', 'string2'],
            'description': 'Example string user setting with options',
            'user_modifiable': True,
        },
        'user_int_setting_options': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'INTEGER',
            'label': 'Integer Setting',
            'default': 0,
            'options': [0, 1],
            'description': 'Example integer user setting with options',
            'user_modifiable': True,
            'widget_attrs': {'class': 'text-success'},
        },
        'user_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'BOOLEAN',
            'label': 'Boolean Setting',
            'default': False,
            'description': 'Example boolean user setting',
            'user_modifiable': True,
        },
        'user_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_USER'],
            'type': 'JSON',
            'label': 'JSON Setting',
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
        'project_user_string_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'STRING',
            'default': '',
            'description': 'Example string project user setting',
        },
        'project_user_int_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'INTEGER',
            'default': '',
            'description': 'Example int project user setting',
        },
        'project_user_bool_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'BOOLEAN',
            'default': '',
            'description': 'Example bool project user setting',
        },
        'project_user_json_setting': {
            'scope': SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT_USER'],
            'type': 'JSON',
            'default': '',
            'description': 'Example json project user setting',
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

    def get_app_alerts(self, user):
        if not settings.EXAMPLE_PROJECT_APP_ALERTS:
            return None
        return [
            {
                'message': 'This is an example app alert with HTML. '
                '<a href="{}">This is a link</a>.'.format(reverse('home')),
                'url': reverse('home'),
                'level': 'INFO',
            },
            {
                'message': 'Another example, this time at the SUCCESS level.',
                'url': reverse('home'),
                'level': 'SUCCESS',
            },
            {
                'message': 'An example WARNING alert without an URL.',
                'url': None,
                'level': 'WARNING',
            },
            {
                'message': 'Finally, a DANGER alert.',
                'url': reverse('home'),
                'level': 'DANGER',
            },
        ]
