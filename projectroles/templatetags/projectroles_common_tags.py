"""Template tags provided by projectroles for use in other apps"""

import mistune

from importlib import import_module
from typing import Any, Optional, Union
from uuid import UUID

from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpRequest
from django.template.loader import get_template
from django.templatetags.static import static
from django.urls import reverse

import projectroles
from projectroles.app_settings import AppSettingAPI
from projectroles.models import (
    Project,
    Role,
    RemoteProject,
    SODARUser,
    SODAR_CONSTANTS,
)
from projectroles.plugins import BackendPluginPoint, PluginAPI
from projectroles.utils import get_display_name as _get_display_name


app_settings = AppSettingAPI()
plugin_api = PluginAPI()
site = import_module(settings.SITE_PACKAGE)
User = get_user_model()

register = template.Library()


# SODAR constants
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']


# SODAR and site operations ----------------------------------------------------


@register.simple_tag
def site_version() -> str:
    """Return the site version"""
    return site.__version__ if hasattr(site, '__version__') else '[UNKNOWN]'


@register.simple_tag
def core_version() -> str:
    """Return the SODAR Core version"""
    return projectroles.__version__


@register.simple_tag
def check_backend(name: str) -> bool:
    """Return True if backend app is available and enabled, else False"""
    return True if name in settings.ENABLED_BACKEND_PLUGINS else False


@register.simple_tag
def get_project_by_uuid(sodar_uuid: Union[str, UUID]) -> Optional[Project]:
    """Return Project by sodar_uuid"""
    return Project.objects.filter(sodar_uuid=sodar_uuid).first()


@register.simple_tag
def get_user_by_uuid(sodar_uuid: Union[str, UUID]) -> Optional[SODARUser]:
    """Return SODARUser by sodar_uuid"""
    return User.objects.filter(sodar_uuid=sodar_uuid).first()


@register.simple_tag
def get_user_by_username(username: str) -> Optional[SODARUser]:
    """Return User by username"""
    return User.objects.filter(username=username).first()


# Django helpers ---------------------------------------------------------------


@register.simple_tag
def get_django_setting(name: str, default: Any = None, js: bool = False) -> Any:
    """
    Return value of Django setting by name or the default value if the setting
    is not found. Return a Javascript-safe value if js=True.
    """
    val = getattr(settings, name, default)
    if js and isinstance(val, bool):
        val = int(val)
    return val


@register.simple_tag
def get_app_setting(
    plugin_name: str,
    setting_name: str,
    project: Optional[Project] = None,
    user: Optional[SODARUser] = None,
) -> Any:
    """Get a project/user specific app setting value from AppSettingAPI"""
    return app_settings.get(plugin_name, setting_name, project, user)


@register.simple_tag
def static_file_exists(path: str) -> bool:
    """Return True/False based on whether a static file exists"""
    return True if finders.find(path) else False


@register.simple_tag
def template_exists(path: str) -> bool:
    """Return True/False based on whether a template exists"""
    try:
        get_template(path)
        return True
    except template.TemplateDoesNotExist:
        return False


@register.simple_tag
def get_full_url(request: HttpRequest, url: str) -> str:
    """Get full URL based on a local URL"""
    return request.scheme + '://' + request.get_host() + url


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_display_name(
    key: str, title: bool = False, count: int = 1, plural: bool = False
) -> str:
    """Return display name from SODAR_CONSTANTS"""
    return _get_display_name(key, title, count, plural)


@register.simple_tag
def get_role_display_name(
    role: Role, project: Project, title: bool = False
) -> str:
    """
    Return display name for role assignment.

    :param role: Role object
    :param project: Project object for context (to support inheritance)
    :param title: Return in title case if True (boolean)
    """
    role_suffix = role.name.split(' ')[1]
    if title:
        role_suffix = role_suffix.title()
    return f'{_get_display_name(project.type, title=title)} {role_suffix}'


@register.simple_tag
def get_project_title_html(project: Project) -> str:
    """Return HTML version of the full project title including parents"""
    ret = ''
    if project.get_parents():
        ret += ' / '.join(project.full_title.split(' / ')[:-1]) + ' / '
    ret += project.title
    return ret


@register.simple_tag
def get_project_link(
    project: str,
    full_title: bool = False,
    request: Optional[HttpRequest] = None,
) -> str:
    """Return link to project with a simple or full title"""
    remote_icon = ''
    if request:
        remote_icon = get_remote_icon(project, request)
    return (
        '<a href="{}" title="{}" data-toggle="tooltip" '
        'data-placement="top">{}</a>{}'.format(
            reverse(
                'projectroles:detail', kwargs={'project': project.sodar_uuid}
            ),
            project.description if project.description else '',
            project.full_title if full_title else project.title,
            ' ' + remote_icon if remote_icon else '',
        )
    )


@register.simple_tag
def get_user_superuser_icon(tooltip: bool = True) -> str:
    """Return superuser icon for user"""
    ret = ''
    if tooltip:
        ret += '<span title="Superuser" data-toggle="tooltip">'
    ret += (
        '<i class="iconify text-info ml-1" '
        'data-icon="mdi:shield-account"></i>'
    )
    if tooltip:
        ret += '</span>'
    return ret


@register.simple_tag
def get_user_inactive_icon(tooltip: bool = True) -> str:
    """Return inactive icon for user"""
    ret = ''
    if tooltip:
        ret += '<span title="Inactive" data-toggle="tooltip">'
    ret += (
        '<i class="iconify text-secondary ml-1" '
        'data-icon="mdi:account-off"></i>'
    )
    if tooltip:
        ret += '</span>'
    return ret


@register.simple_tag
def get_user_html(user: SODARUser) -> str:
    """Return HTML representation of a User object"""
    email_link = True if user.is_active and user.email else False
    title = user.get_full_name()
    if not user.is_active:
        title += ' (inactive)'
    elif user.is_superuser:
        title += ' (superuser)'
    ret = (
        '<span class="sodar-user-html{}" data-toggle="tooltip" '
        'data-placement="top" title="{}">'.format(
            ' text-secondary' if not user.is_active else '', title
        )
    )
    if email_link:
        ret += f'<a href="mailto:{user.email}">'
    ret += user.username
    if email_link:
        ret += '</a>'
    if user.is_superuser:
        ret += get_user_superuser_icon(False)
    if not user.is_active:
        ret += get_user_inactive_icon(False)
    ret += '</span>'
    return ret


@register.simple_tag
def get_user_badge(user: SODARUser, extra_class: Optional[str] = None) -> str:
    """
    Return badge HTML for a User object.

    :param user: SODARUser object
    :param extra_class: Extra classes to add to element (string, optional)
    :return: String (contains HTML)
    """
    if not user.is_active:
        icon = 'mdi:account-off'
        variant = 'secondary'
        user_class = 'inactive'
    elif user.is_superuser:
        icon = 'mdi:shield-account'
        variant = 'info'
        user_class = 'superuser'
    else:
        icon = 'mdi:account'
        variant = 'primary'
        user_class = 'active'
    email = True if user.is_active and user.email else False
    if extra_class and not extra_class.startswith(' '):
        extra_class = ' ' + extra_class
    elif not extra_class:
        extra_class = ''
    ret = (
        f'<span class="badge badge-{variant} sodar-obj-badge '
        f'sodar-user-badge sodar-user-badge-{user_class}{extra_class}" '
        f'title="{user.get_full_name()}" data-toggle="tooltip" '
        f'data-uuid="{user.sodar_uuid}">'
        f'<i class="iconify" data-icon="{icon}"></i> '
    )
    if email:
        ret += f'<a class="text-white" href="mailto:{user.email}">'
    ret += user.username
    if email:
        ret += '</a>'
    ret += '</span>'
    return ret


@register.simple_tag
def get_project_badge(
    project: Project,
    variant: Optional[str] = None,
    can_view: bool = True,
    extra_class: Optional[str] = None,
) -> str:
    """
    Return badge HTML for a Project object.

    :param project: Project object
    :param variant: Badge variant (string)
    :param can_view: Display project link if True (bool)
    :param extra_class: Extra classes to add to element (string, optional)
    :return: String (contains HTML)
    """
    if not can_view:
        variant = 'secondary'
    elif not variant:
        variant = 'info'
    extra_class = (' ' + extra_class) if extra_class else ''
    ret = (
        f'<span class="badge badge-{variant.lower()} sodar-obj-badge '
        f'sodar-project-badge{extra_class}" title="{project.full_title}" '
        f'data-toggle="tooltip">'
    )
    if project.is_project():
        icon = 'mdi:cube'
    else:
        icon = 'mdi:rhombus-split'
    ret += f'<i class="iconify" data-icon="{icon}"></i> '
    if can_view:
        url = reverse(
            'projectroles:detail', kwargs={'project': project.sodar_uuid}
        )
        ret += f'<a href="{url}">{project.title}</a>'
    else:
        ret += project.title
    ret += '</span>'
    return ret


@register.simple_tag
def get_backend_include(backend_name: str, include_type: str = 'js') -> str:
    """
    Return import string for backend app Javascript or CSS. Returns empty string
    if not found.
    """
    # TODO: Replace with get_app_plugin() and if None check
    # TODO: once get_app_plugin() can be used for backend plugins
    # TODO: Don't forget to remove ObjectDoesNotExist import
    try:
        plugin = BackendPluginPoint.get_plugin(backend_name)
    except ObjectDoesNotExist:
        return ''

    include = ''
    include_string = ''
    try:
        if include_type == 'js':
            include = plugin.javascript_url
            include_string = '<script type="text/javascript" src="{}"></script>'
        elif include_type == 'css':
            include = plugin.css_url
            include_string = (
                '<link rel="stylesheet" type="text/css" href="{}"/>'
            )
    except AttributeError:
        return ''

    if include and finders.find(include):
        return include_string.format(static(include))

    return ''


@register.simple_tag
def get_history_dropdown(obj: Any, project: Optional[Project] = None) -> str:
    """Return link to object timeline events within project"""
    timeline = plugin_api.get_backend_api('timeline_backend')
    if not timeline:
        return ''
    url = timeline.get_object_url(obj, project)
    return (
        '<a class="dropdown-item sodar-pr-role-link-history" href="{}">\n'
        '<i class="iconify" data-icon="mdi:clock-time-eight-outline"></i> '
        'History</a>\n'.format(url)
    )


@register.simple_tag
def highlight_search_term(item: str, terms: list[str]) -> str:
    """Return string with search term highlighted"""
    # Skip highlighting for multiple terms (at least for now)
    if isinstance(terms, list) and len(terms) > 1:
        return item
    elif isinstance(terms, list) and len(terms) == 1:
        term = terms[0]
    else:
        term = terms  # Old implementation
    if not term:  # If something goes wrong and we end up with no search term
        return item

    def get_highlights(item):
        pos = item.lower().find(term.lower())
        tl = len(term)
        if pos == -1:
            return item  # Nothing to highlight
        ret = item[:pos]
        ret += (
            '<span class="sodar-search-highlight">'
            + item[pos : pos + tl]
            + '</span>'
        )
        if len(item[pos + tl :]) > 0:
            ret += get_highlights(item[pos + tl :])
        return ret

    return get_highlights(item)


@register.simple_tag
def get_info_link(content: str, html: bool = False) -> str:
    """Return info popover link icon"""
    return (
        '<a class="sodar-info-link" tabindex="0" data-toggle="popover" '
        'data-trigger="focus" data-placement="top" data-content="{}" {}>'
        '<i class="iconify text-info" data-icon="mdi:information"></i>'
        '</a>'.format(content, 'data-html="true"' if html else '')
    )


@register.simple_tag
def get_remote_icon(project: Project, request: HttpRequest) -> str:
    """Get remote project icon HTML"""
    if project.is_remote() and request.user.is_superuser:
        remote_project = RemoteProject.objects.filter(
            project=project, site__mode=SITE_MODE_SOURCE
        ).first()
        if remote_project:
            return (
                '<i class="iconify {} mx-1 '
                'sodar-pr-remote-project-icon" data-icon="mdi:cloud" '
                'title="{} project from '
                '{}" data-toggle="tooltip" data-placement="top">'
                '</i>'.format(
                    'text-danger' if project.is_revoked() else 'text-info',
                    'REVOKED remote' if project.is_revoked() else 'Remote',
                    remote_project.site.name,
                )
            )
    return ''


@register.simple_tag
def render_markdown(raw_markdown: str) -> str:
    """Markdown field rendering helper"""
    return mistune.html(raw_markdown)


@register.filter
def force_wrap(s: str, length: int) -> str:
    """Force wrapping of string"""
    # If string contains spaces or hyphens, leave wrapping to browser
    if not {' ', '-'}.intersection(s) and len(s) > length:
        return '<wbr />'.join(
            [s[i : i + length] for i in range(0, len(s), length)]
        )
    return s


# General helpers  -------------------------------------------------------------


@register.simple_tag
def get_class(obj: any, lower: bool = False) -> str:
    """Return object class as string"""
    c = obj.__class__.__name__
    return c.lower() if lower else c


@register.filter
def split(s: str, sep: str) -> list:
    """Split string by separator"""
    return s.split(sep)
