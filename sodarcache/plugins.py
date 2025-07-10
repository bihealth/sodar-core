"""Plugins for the sodarcache app"""

# Projectroles dependency
from projectroles.plugins import BackendPluginPoint

from sodarcache.api import SODARCacheAPI


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (used as plugin ID)
    name = 'sodar_cache'

    #: Title (used in templates)
    title = 'SODAR Cache Backend'

    #: Iconify icon
    icon = 'mdi:basket-outline'

    #: Description string
    description = (
        'SODAR Cache backend for caching and aggregating data from external '
        'databases'
    )

    def get_api(self, **kwargs) -> SODARCacheAPI:
        """Return API entry point object."""
        return SODARCacheAPI()
