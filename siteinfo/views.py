import logging
from urllib.parse import ParseResult

from django.conf import settings
from django.contrib import auth
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.models import (
    Project,
    RemoteSite,
    SODAR_CONSTANTS,
    AUTH_TYPE_LDAP,
    AUTH_TYPE_LOCAL,
    AUTH_TYPE_OIDC,
)
from projectroles.plugins import PluginAPI
from projectroles.views import LoggedInPermissionMixin

from siteinfo.constants import CORE_SETTINGS


logger = logging.getLogger(__name__)
plugin_api = PluginAPI()
User = auth.get_user_model()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']


class SiteInfoView(LoggedInPermissionMixin, TemplateView):
    """Site info view"""

    permission_required = 'siteinfo.view_info'
    template_name = 'siteinfo/site_info.html'

    @classmethod
    def _get_settings(cls, keys: list[str]) -> dict:
        ret = {}
        for k in keys:
            if hasattr(settings, k):
                v = getattr(settings, k)
                if isinstance(v, ParseResult):
                    v = v.geturl()
                ret[k] = {'value': v, 'set': True}
            else:
                ret[k] = {'set': False}
        return ret

    @classmethod
    def _get_plugin_settings(cls, p_list: list) -> dict:
        ret = {}
        for p in p_list:
            ret[p] = {}
            if p.info_settings:
                try:
                    ret[p]['settings'] = cls._get_settings(p.info_settings)
                except Exception as ex:
                    ret[p]['error'] = str(ex)
                    logger.error(
                        f'Exception in _get_settings() for {p.name}: {ex}'
                    )
        return ret

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Project statistics
        context['project_count'] = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT
        ).count()
        context['category_count'] = Project.objects.filter(
            type=PROJECT_TYPE_CATEGORY
        ).count()
        context['project_archive_count'] = Project.objects.filter(
            type=PROJECT_TYPE_PROJECT, archive=True
        ).count()

        # User statistics
        users = User.objects.all()
        context['user_total_count'] = users.count()
        context['user_ldap_count'] = len(
            [u for u in users if u.get_auth_type() == AUTH_TYPE_LDAP]
        )
        context['user_oidc_count'] = len(
            [u for u in users if u.get_auth_type() == AUTH_TYPE_OIDC]
        )
        local_users = [
            u
            for u in users
            if u.get_auth_type() == AUTH_TYPE_LOCAL and not u.is_superuser
        ]
        context['user_local_count'] = len(local_users)
        context['user_admin_count'] = User.objects.filter(
            is_superuser=True
        ).count()
        context['user_inactive_count'] = User.objects.filter(
            is_active=False
        ).count()

        # App plugins
        project_plugins = plugin_api.get_active_plugins('project_app')
        backend_plugins = plugin_api.get_active_plugins('backend')
        site_plugins = plugin_api.get_active_plugins('site_app')

        # Plugin statistics
        context['project_plugins'] = self._get_plugin_settings(project_plugins)
        context['site_plugins'] = self._get_plugin_settings(site_plugins)
        context['backend_plugins'] = self._get_plugin_settings(backend_plugins)

        # Basic site info
        context['site_title'] = settings.SITE_TITLE
        context['site_subtitle'] = settings.SITE_SUBTITLE
        context['site_instance_title'] = settings.SITE_INSTANCE_TITLE

        # Remote site info
        context['site_mode'] = settings.PROJECTROLES_SITE_MODE

        if settings.PROJECTROLES_SITE_MODE == SITE_MODE_SOURCE:
            context['site_target_count'] = RemoteSite.objects.filter(
                mode=SITE_MODE_TARGET
            ).count()

        # Core settings
        context['settings_core'] = self._get_settings(CORE_SETTINGS)
        # TODO: Add LDAP settings?
        return context
