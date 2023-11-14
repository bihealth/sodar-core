"""Plugins for the tokens app"""

# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from tokens.urls import urlpatterns


class ProjectAppPlugin(SiteAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    name = 'tokens'

    title = 'API Tokens'

    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:key-chain-variant'

    entry_point_url_id = 'tokens:list'

    description = 'API Token Management'

    #: Required permission for accessing the app
    app_permission = 'tokens.access'
