"""Plugins for the adminalerts app"""

from django.urls import reverse
from django.utils import timezone

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import SiteAppPluginPoint

from adminalerts.models import AdminAlert
from adminalerts.urls import urlpatterns


# SODAR constants
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'adminalerts'

    #: Title (used in templates)
    title = 'Admin Alerts'

    #: UI URLs
    urls = urlpatterns

    #: App settings definition
    app_settings = {
        'notify_email_alert': {
            'scope': APP_SETTING_SCOPE_USER,
            'type': 'BOOLEAN',
            'default': True,
            'label': 'Receive email for admin alerts',
            'description': (
                'Receive email for important administrator alerts regarding '
                'e.g. site downtime.'
            ),
            'user_modifiable': True,
            'global': False,
        }
    }

    #: Iconify icon
    icon = 'mdi:alert'

    #: Description string
    description = 'Administrator alerts to be shown for users'

    #: Entry point URL ID
    entry_point_url_id = 'adminalerts:list'

    #: Required permission for displaying the app
    app_permission = 'adminalerts.create_alert'

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = ['ADMINALERTS_PAGINATION']

    def get_statistics(self):
        return {
            'alert_count': {
                'label': 'Alerts',
                'value': AdminAlert.objects.all().count(),
            }
        }

    def get_messages(self, user=None):
        """
        Return a list of messages to be shown to users.
        :param user: User object (optional)
        :return: List of dicts or empty list if no messages
        """
        messages = []
        alerts = AdminAlert.objects.filter(
            active=True, date_expire__gte=timezone.now()
        ).order_by('-pk')

        for a in alerts:
            content = (
                '<i class="iconify" data-icon="mdi:alert"></i> ' + a.message
            )
            if a.description.raw and user and user.is_authenticated:
                content += (
                    '<span class="pull-right"><a href="{}" class="text-info">'
                    '<i class="iconify" data-icon="mdi:arrow-right-circle">'
                    '</i> Details</a>'.format(
                        reverse(
                            'adminalerts:detail',
                            kwargs={'adminalert': a.sodar_uuid},
                        )
                    )
                )
            messages.append(
                {
                    'content': content,
                    'color': 'info',
                    'dismissable': False,
                    'require_auth': a.require_auth,
                }
            )
        return messages
