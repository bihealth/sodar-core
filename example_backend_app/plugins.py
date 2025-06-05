"""Plugins for the example_backend_app Django app"""

# Projectroles dependency
from projectroles.plugins import BackendPluginPoint

from example_backend_app.api import ExampleAPI


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (used as plugin ID)
    name = 'example_backend_app'

    #: Title (used in templates)
    title = 'Example Backend App'

    #: Iconify icon
    icon = 'mdi:code-braces'

    #: Description string
    description = 'Example Backend API'

    #: URL of optional javascript file to be included
    javascript_url = 'example_backend_app/js/greeting.js'

    #: URL of optional css file to be included
    css_url = 'example_backend_app/css/greeting.css'

    def get_api(self, **kwargs) -> ExampleAPI:
        """Return API entry point object."""
        return ExampleAPI(**kwargs)

    def get_statistics(self) -> dict:
        return {
            'backend_example_stat': {'label': 'Backend example', 'value': True}
        }
