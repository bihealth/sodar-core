"""Ajax views for the siteinfo app"""

import logging

# from django.views.decorators.http import require_GET

from rest_framework.response import Response

from projectroles.plugins import PluginAPI
from projectroles.views_ajax import SODARBasePermissionAjaxView


logger = logging.getLogger(__name__)
plugin_api = PluginAPI()


# @require_GET()
class PluginStatisticsAjaxView(SODARBasePermissionAjaxView):
    """Site info ajax view"""

    permission_required = 'siteinfo.view_info'

    def get(self, request, **kwargs):
        # Retrieve all plugins
        plugins = (
            plugin_api.get_active_plugins('project_app')
            + plugin_api.get_active_plugins('backend')
            + plugin_api.get_active_plugins('site_app')
        )
        plugins.sort(key=lambda p: p.title)
        ret = {}
        for p in plugins:
            try:
                stats = p.get_statistics()
                if len(stats):
                    ret[p.name] = {
                        'title': p.title,
                        'icon': p.icon,
                        'stats': stats,
                    }
            except Exception as ex:
                ret[p.name] = {
                    'title': p.title,
                    'icon': p.icon,
                    'error': str(ex)
                }
                logger.error(f'Exception in {p.name}.get_statistics(): {ex}')
        return Response(ret)
