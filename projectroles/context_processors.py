"""Context processors for the projectroles app"""

from math import ceil

from django.conf import settings

from projectroles.plugins import get_active_plugins, get_backend_api
from projectroles.urls import urlpatterns
from projectroles.utils import ROLE_URLS


SIDEBAR_ICON_MIN_SIZE = 18
SIDEBAR_ICON_MAX_SIZE = 42


def urls_processor(request):
    """Context processor for providing projectroles URLs for the sidebar"""
    return {
        'projectroles_urls': urlpatterns,
        'role_urls': ROLE_URLS,
    }


def site_app_processor(request):
    """
    Context processor for providing site apps for the site titlebar dropdown.
    """
    site_apps = get_active_plugins('site_app')
    return {
        'site_apps': [
            a
            for a in site_apps
            if not a.app_permission or request.user.has_perm(a.app_permission)
        ],
    }


def app_alerts_processor(request):
    """
    Context processor for checking app alert status.
    """
    if request.user and request.user.is_authenticated:
        app_alerts = get_backend_api('appalerts_backend')
        if app_alerts:
            return {
                'app_alerts': app_alerts.get_model()
                .objects.filter(user=request.user, active=True)
                .count()
            }
    return {'app_alerts': 0}


def sidebar_processor(request):
    """
    Context processor for providing sidebar information.
    """
    sidebar_icon_size = sorted(
        [
            SIDEBAR_ICON_MIN_SIZE,
            getattr(settings, 'PROJECTROLES_SIDEBAR_ICON_SIZE', 32),
            SIDEBAR_ICON_MAX_SIZE,
        ]
    )[1]
    return {
        'sidebar_icon_size': sidebar_icon_size,
        'sidebar_notch_pos': ceil(sidebar_icon_size / 3),
        'sidebar_notch_size': min(ceil(sidebar_icon_size / 2), 12),
        'sidebar_padding': ceil(sidebar_icon_size / 4.5),
    }
