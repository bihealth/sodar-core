"""Plugins for the appalerts app"""

# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint, BackendPluginPoint

from appalerts.api import AppAlertAPI
from appalerts.urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Site plugin for application alerts"""

    #: Name (used as plugin ID)
    name = 'appalerts'

    #: Title (used in templates)
    title = 'App Alerts'

    #: UI URLs
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:alert-octagram'

    #: Description string
    description = 'App-specific alerts for users'

    #: Entry point URL ID
    entry_point_url_id = 'appalerts:list'

    #: Required permission for displaying the app
    app_permission = 'appalerts.view_alerts'


class BackendPlugin(BackendPluginPoint):
    """Backend plugin for application alerts"""

    #: Name (used as plugin ID)
    name = 'appalerts_backend'

    #: Title (used in templates)
    title = 'App Alerts Backend'

    #: Iconify icon
    icon = 'mdi:alert-octagram-outline'

    #: Description string
    description = 'App Alerts backend for creating and accessing alerts'

    #: URL of optional javascript file to be included
    javascript_url = 'appalerts/js/appalerts.js'

    def get_api(self, **kwargs) -> AppAlertAPI:
        """Return API entry point object"""
        return AppAlertAPI()
