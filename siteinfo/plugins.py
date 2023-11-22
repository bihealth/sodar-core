# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from siteinfo.urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'siteinfo'

    #: Title (used in templates)
    title = 'Site Info'

    #: UI URLs
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:bar-chart'

    #: Description string
    description = 'Site information and app statistics'

    #: Entry point URL ID
    entry_point_url_id = 'siteinfo:info'

    #: Required permission for displaying the app
    app_permission = 'siteinfo:view_info'
