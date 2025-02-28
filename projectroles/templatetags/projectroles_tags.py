"""Template tags for internal use within the projectroles app"""

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from projectroles.app_settings import AppSettingAPI
from projectroles.models import RemoteProject, SODAR_CONSTANTS
from projectroles.plugins import get_active_plugins
from projectroles.utils import AppLinkContent


register = template.Library()
app_links = AppLinkContent()
app_settings = AppSettingAPI()


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
REMOTE_LEVEL_NONE = SODAR_CONSTANTS['REMOTE_LEVEL_NONE']
REMOTE_LEVEL_REVOKED = SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED']

# Local constants
APP_NAME = 'projectroles'
# Behaviour for certain levels has not been specified/implemented yet
ACTIVE_LEVEL_TYPES = [
    SODAR_CONSTANTS['REMOTE_LEVEL_NONE'],
    SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
]


# SODAR and site operations ----------------------------------------------------


@register.simple_tag
def sodar_constant(value):
    """Get value from SODAR_CONSTANTS"""
    return SODAR_CONSTANTS[value] if value in SODAR_CONSTANTS else None


# TODO: Refactor into get_plugins(type)
@register.simple_tag
def get_backend_plugins():
    """Get active backend plugins"""
    return get_active_plugins('backend')


@register.simple_tag
def get_site_app_messages(user):
    """Get messages from site apps"""
    plugins = get_active_plugins('site_app')
    ret = []
    for p in plugins:
        ret += p.get_messages(user)
    return ret


@register.simple_tag
def get_remote_project_obj(site, project):
    """Return RemoteProject object for RemoteSite and Project"""
    try:
        return RemoteProject.objects.get(
            site=site, project_uuid=project.sodar_uuid
        )
    except RemoteProject.DoesNotExist:
        return None


@register.simple_tag
def allow_project_creation():
    """Check whether creating a project is allowed on the site"""
    if (
        settings.PROJECTROLES_SITE_MODE == SODAR_CONSTANTS['SITE_MODE_TARGET']
        and not settings.PROJECTROLES_TARGET_CREATE
    ):
        return False
    return True


@register.simple_tag
def is_app_visible(plugin, project, user):
    """Check if app should be visible for user in a specific project"""
    can_view_app = user.has_perm(plugin.app_permission, project)
    app_hidden = False
    if plugin.name in getattr(settings, 'PROJECTROLES_HIDE_PROJECT_APPS', []):
        app_hidden = True
    if (
        can_view_app
        and not app_hidden
        and (project.type == PROJECT_TYPE_PROJECT or plugin.category_enable)
    ):
        return True
    return False


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_app_link_state(app_plugin, app_name, url_name):
    """
    Return "active" if plugin matches app_name and url_name is found in
    app_plugin.urls.
    """
    if app_plugin.name.startswith(app_name) and url_name in [
        u.name for u in getattr(app_plugin, 'urls', [])
    ]:
        return 'active'
    # HACK for remote site views, see issue #1336
    if (
        app_name == APP_NAME
        and app_plugin.name == 'remotesites'
        and url_name.startswith('remote_')
    ):
        return 'active'
    return ''


@register.simple_tag
def get_pr_link_state(app_urls, request, link_names=None):
    """
    Version of get_app_link_state() to be used within the projectroles app.
    If link_names is set, only return "active" if url_name is found in
    link_names.
    """
    if request.resolver_match.app_name != APP_NAME:
        return ''
    url_name = request.resolver_match.url_name
    if url_name in [u.name for u in app_urls]:
        if link_names:
            if not isinstance(link_names, list):
                link_names = [link_names]
            if url_name not in link_names:
                return ''
        return 'active'
    return ''


@register.simple_tag
def get_help_highlight(user):
    """
    Return classes to highlight navbar help link if user has recently signed in
    """
    if user.__class__.__name__ == 'User' and user.is_authenticated:
        delta_days = (timezone.now() - user.date_joined).days
        highlight = getattr(settings, 'PROJECTROLES_HELP_HIGHLIGHT_DAYS', 7)
        if delta_days < highlight:
            return 'font-weight-bold text-warning'
    return ''


@register.simple_tag
def get_login_info():
    """Return HTML info for the login page"""
    ret = '<p>Please log in'

    if getattr(settings, 'ENABLE_LDAP', False):
        ret += ' using your ' + settings.AUTH_LDAP_DOMAIN_PRINTABLE
        if (
            getattr(settings, 'ENABLE_LDAP_SECONDARY', False)
            and settings.AUTH_LDAP2_DOMAIN_PRINTABLE
        ):
            ret += ' or ' + settings.AUTH_LDAP2_DOMAIN_PRINTABLE
        ret += (
            ' account. Enter your user name as <code>username@{}'
            '</code>'.format(getattr(settings, 'AUTH_LDAP_USERNAME_DOMAIN', ''))
        )
        if (
            settings.ENABLE_LDAP_SECONDARY
            and settings.AUTH_LDAP2_USERNAME_DOMAIN
        ):
            ret += ' or <code>username@{}</code>'.format(
                settings.AUTH_LDAP2_USERNAME_DOMAIN
            )
        if getattr(settings, 'PROJECTROLES_ALLOW_LOCAL_USERS', False):
            ret += (
                '. To access the site with local account enter your user '
                'name as <code>username</code>'
            )

    ret += '.</p>'
    return ret


@register.simple_tag
def get_target_project_select(site, project):
    """Return remote target project level selection HTML"""
    current_level = None

    try:
        rp = RemoteProject.objects.get(
            site__mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            site=site,
            project_uuid=project.sodar_uuid,
        )
        current_level = rp.level
    except RemoteProject.DoesNotExist:
        pass

    ret = (
        '<select class="form-control form-control-sm" '
        'name="remote_access_{project}" '
        'id="sodar-pr-remote-project-select-{project}">'
        '\n'.format(project=project.sodar_uuid)
    )

    for level in ACTIVE_LEVEL_TYPES:
        selected = False
        if (
            level == REMOTE_LEVEL_NONE
            and current_level
            and current_level != REMOTE_LEVEL_NONE
        ):
            legend = SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][
                REMOTE_LEVEL_REVOKED
            ]
            level_val = REMOTE_LEVEL_REVOKED
        else:
            legend = SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][level]
            level_val = level

        if level == current_level or (
            level == SODAR_CONSTANTS['REMOTE_LEVEL_NONE'] and not current_level
        ):
            selected = True

        ret += '<option value="{}" {}>{}</option>\n'.format(
            level_val, 'selected' if selected else '', legend
        )

    ret += '</select>\n'
    return ret


@register.simple_tag
def get_remote_access_legend(level):
    """Return legend text for remote project access level"""
    if level not in SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS']:
        return 'N/A'
    return SODAR_CONSTANTS['REMOTE_ACCESS_LEVELS'][level]


@register.simple_tag
def get_sidebar_app_legend(title):
    """Return sidebar link legend HTML"""
    return '<br />'.join(title.split(' '))


@register.simple_tag
def get_admin_warning():
    """Return Django admin warning HTML"""
    ret = (
        '<p class="text-danger">Editing database objects other than users '
        'directly in the Django admin view is <strong>not</strong> '
        'recommended!</p>'
    )
    ret += (
        '<p class="text-danger">Actions taken in the admin view may '
        'result in system malfunction or data loss! Please proceed with '
        'caution.</p>'
    )
    ret += (
        '<p><a class="btn btn-danger pull-right" role="button" '
        'target="_blank" href="{}" id="sodar-pr-btn-admin-continue">'
        '<i class="iconify" data-icon="mdi:cogs"></i> Continue to Django Admin'
        '</a></p>'.format(reverse('admin:index'))
    )
    return ret


@register.simple_tag
def get_user_links(request):
    """Return user dropdown links"""
    if isinstance(request, str):
        return []
    return app_links.get_user_links(
        request.user,
        app_name=request.resolver_match.app_name,
        url_name=request.resolver_match.url_name,
    )


@register.simple_tag
def get_project_app_links(request, project=None):
    """Return sidebar links"""
    if isinstance(request, str):
        return []
    return app_links.get_project_links(
        request.user,
        project,
        app_name=request.resolver_match.app_name,
        url_name=request.resolver_match.url_name,
    )
