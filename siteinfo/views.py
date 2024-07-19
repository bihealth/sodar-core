import logging
from urllib.parse import ParseResult

from django.conf import settings
from django.contrib import auth
from django.views.generic import TemplateView

# Projectroles dependency
from projectroles.models import Project, RemoteSite, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins
from projectroles.views import LoggedInPermissionMixin


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SYSTEM_USER_GROUP = SODAR_CONSTANTS['SYSTEM_USER_GROUP']

# Local constants
CORE_SETTINGS = [
    'ADMINS',
    'ALLOWED_HOSTS',
    'APPS_DIR',
    'AUTH_LDAP_CA_CERT_FILE',
    'AUTH_LDAP_DOMAIN_PRINTABLE',
    'AUTH_LDAP_SERVER_URI',
    'AUTH_LDAP_START_TLS',
    'AUTH_LDAP_USER_SEARCH_BASE',
    'AUTH_LDAP_USERNAME_DOMAIN',
    'AUTH_LDAP2_CA_CERT_FILE',
    'AUTH_LDAP2_DOMAIN_PRINTABLE',
    'AUTH_LDAP2_SERVER_URI',
    'AUTH_LDAP2_START_TLS',
    'AUTH_LDAP_USER_SEARCH_BASE',
    'AUTH_LDAP2_USERNAME_DOMAIN',
    'DEBUG',
    'EMAIL_BACKEND',
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_SENDER',
    'ENABLE_LDAP',
    'ENABLE_LDAP_SECONDARY',
    'ENABLE_OIDC',
    'ENABLED_BACKEND_PLUGINS',
    'ICONIFY_JSON_ROOT',
    'INSTALLED_APPS',
    'LANGUAGE_CODE',
    'LDAP_ALT_DOMAINS',
    'LDAP_DEBUG',
    'LOGGING_APPS',
    'LOGGING_FILE_PATH',
    'LOGGING_LEVEL',
    'MANAGERS',
    'MIDDLEWARE',
    'PROJECTROLES_ALLOW_ANONYMOUS',
    'PROJECTROLES_ALLOW_LOCAL_USERS',
    'PROJECTROLES_BROWSER_WARNING',
    'PROJECTROLES_CUSTOM_JS_INCLUDES',
    'PROJECTROLES_CUSTOM_CSS_INCLUDES',
    'PROJECTROLES_DEFAULT_ADMIN',
    'PROJECTROLES_DELEGATE_LIMIT',
    'PROJECTROLES_DISABLE_CATEGORIES',
    'PROJECTROLES_DISABLE_CDN_INCLUDES',
    'PROJECTROLES_EMAIL_SENDER_REPLY',
    'PROJECTROLES_ENABLE_PROFILING',
    'PROJECTROLES_ENABLE_SEARCH',
    'PROJECTROLES_HELP_HIGHLIGHT_DAYS',
    'PROJECTROLES_HIDE_PROJECT_APPS',
    'PROJECTROLES_INLINE_HEAD_INCLUDE',
    'PROJECTROLES_INVITE_EXPIRY_DAYS',
    'PROJECTROLES_KIOSK_MODE',
    'PROJECTROLES_SEARCH_PAGINATION',
    'PROJECTROLES_SECRET_LENGTH',
    'PROJECTROLES_SEND_EMAIL',
    'PROJECTROLES_SIDEBAR_ICON_SIZE',
    'PROJECTROLES_SITE_MODE',
    'PROJECTROLES_TEMPLATE_INCLUDE_PATH',
    'PROJECTROLES_TARGET_CREATE',
    'PROJECTROLES_TARGET_SYNC_ENABLE',
    'PROJECTROLES_TARGET_SYNC_INTERVAL',
    'ROOT_DIR',
    'SITE_PACKAGE',
    'SITE_TITLE',
    'SITE_SUBTITLE',
    'SITE_INSTANCE_TITLE',
    'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT',
    'SOCIAL_AUTH_OIDC_KEY',
    'SOCIAL_AUTH_OIDC_USERNAME_KEY',
    'SODAR_API_ALLOWED_VERSIONS',
    'SODAR_API_DEFAULT_VERSION',
    'SODAR_API_DEFAULT_HOST',
    'SODAR_API_MEDIA_TYPE',
    'STATICFILES_DIRS',
    'STATICFILES_FINDERS',
    'TEMPLATES',
    'TIME_ZONE',
    'USE_TZ',
]


# Access Django user model
User = auth.get_user_model()

logger = logging.getLogger(__name__)


class SiteInfoView(LoggedInPermissionMixin, TemplateView):
    """Site info view"""

    permission_required = 'siteinfo.view_info'
    template_name = 'siteinfo/site_info.html'

    @classmethod
    def _get_settings(cls, keys):
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
    def _get_plugin_stats(cls, p_list):
        ret = {}
        for p in p_list:
            try:
                ret[p] = {'stats': p.get_statistics(), 'settings': {}}
            except Exception as ex:
                ret[p] = {'error': str(ex)}
                logger.error(
                    'Exception in {}.get_statistics(): {}'.format(p.name, ex)
                )
            if p.info_settings:
                try:
                    ret[p]['settings'] = cls._get_settings(p.info_settings)
                except Exception as ex:
                    logger.error(
                        'Exception in _get_settings() for {}: {}'.format(
                            p.name, ex
                        )
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
        context['user_total_count'] = User.objects.all().count()
        context['user_ldap_count'] = User.objects.exclude(
            groups__name__in=['', SYSTEM_USER_GROUP]
        ).count()
        context['user_local_count'] = User.objects.filter(
            groups__name__in=['', SYSTEM_USER_GROUP]
        ).count()
        context['user_admin_count'] = User.objects.filter(
            is_superuser=True
        ).count()

        # App plugins
        project_plugins = get_active_plugins('project_app')
        backend_plugins = get_active_plugins('backend')
        site_plugins = get_active_plugins('site_app')

        # Plugin statistics
        context['project_plugins'] = self._get_plugin_stats(project_plugins)
        context['site_plugins'] = self._get_plugin_stats(site_plugins)
        context['backend_plugins'] = self._get_plugin_stats(backend_plugins)

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
