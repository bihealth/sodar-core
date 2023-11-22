"""Plugins for the tokens app"""

# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from tokens.urls import urlpatterns


class ProjectAppPlugin(SiteAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    #: Name (used as plugin ID)
    name = 'tokens'

    #: Title (used in templates)
    title = 'API Tokens'

    #: UI URLs
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:key-chain-variant'

    #: Entry point URL ID
    entry_point_url_id = 'tokens:list'

    #: Description string
    description = 'API Token Management'

    #: Required permission for accessing the app
    app_permission = 'tokens.access'
