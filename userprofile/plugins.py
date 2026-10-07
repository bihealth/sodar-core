"""Plugins for the userprofile app"""

from typing import Optional

from django.contrib.auth import get_user_model

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import SiteAppPluginPoint, PluginAppSettingDef

from userprofile.urls import urls_detail, urls_list


User = get_user_model()


# SODAR constants
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'userprofile'

    #: Title (used in templates)
    title = 'User Profile'

    #: UI URLs
    urls = urls_detail

    #: Iconify icon
    icon = 'mdi:account-details'

    #: Description string
    description = 'Project User Profile'

    #: Entry point URL ID
    entry_point_url_id = 'userprofile:detail'

    #: Required permission for displaying the app
    app_permission = 'userprofile.view_detail'

    #: App setting definitions
    app_settings = [
        PluginAppSettingDef(
            name='enable_project_uuid_copy',
            scope=APP_SETTING_SCOPE_USER,
            type=APP_SETTING_TYPE_BOOLEAN,
            label='Display project UUID copying link',
            description='Display link in project header to copy project UUID '
            'into the clipboard.',
            default=False,
        )
    ]

    def get_messages(self, user: Optional[User] = None) -> list[dict]:
        """
        Return a list of messages to be shown to users.
        :param user: User object (optional)
        :return: List of dicts or and empty list if no messages
        """
        messages = []
        return messages


class UserListSiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'userprofile_list'

    #: Title (used in templates)
    title = 'User List'

    #: UI URLs
    urls = urls_list

    #: Iconify icon
    icon = 'mdi:account-search'

    #: Description string
    description = 'List of users on the site'

    #: Entry point URL ID
    entry_point_url_id = 'userprofile:list'

    #: Required permission for displaying the app
    app_permission = 'userprofile.view_list'
