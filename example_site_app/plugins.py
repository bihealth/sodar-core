# Projectroles dependency
from projectroles.plugins import SiteAppPluginPoint

from example_site_app.urls import urlpatterns


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'example_site_app'

    #: Title (used in templates)
    title = 'Example Site App'

    #: UI URLs
    urls = urlpatterns

    #: Iconify icon
    icon = 'mdi:rocket-launch-outline'

    #: Description string
    description = 'Example site-wide app'

    #: Entry point URL ID
    entry_point_url_id = 'example_site_app:example'

    #: Required permission for displaying the app
    app_permission = 'example_site_app.view_data'

    def get_messages(self, user=None):
        """
        Return a list of messages to be shown to users.
        :param user: User object (optional)
        :return: List of dicts or and empty list if no messages
        """
        messages = []
        return messages
