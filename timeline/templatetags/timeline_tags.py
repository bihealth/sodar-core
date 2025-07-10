"""Template tags for the timeline app"""

import logging

from typing import Optional

from django import template
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from django.utils.timezone import localtime

from djangoplugins.models import Plugin

# Projectroles dependency
from projectroles.models import Project
from projectroles.plugins import ProjectAppPluginPoint

from timeline.api import TimelineAPI
from timeline.models import TimelineEvent


logger = logging.getLogger(__name__)
timeline = TimelineAPI()
register = template.Library()


ICON_PROJECTROLES = 'mdi:cube'
ICON_UNKNOWN_APP = 'mdi:help-circle'
STATUS_STYLES = {
    'OK': 'bg-success',
    'INIT': 'bg-secondary',
    'SUBMIT': 'bg-warning',
    'FAILED': 'bg-danger',
    'INFO': 'bg-info',
    'CANCEL': 'bg-dark',
}


# Event helpers ----------------------------------------------------------------


@register.simple_tag
def get_timestamp(event: TimelineEvent) -> str:
    """Return printable timestamp of event in local timezone"""
    try:
        return localtime(event.get_timestamp()).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:  # Handle error cases where TimelineEventStatus is missing
        return 'N/A'


@register.simple_tag
def get_event_name(event: TimelineEvent) -> str:
    """Return timeline event name in a user friendly format"""
    return event.event_name.replace('_', ' ').title()


@register.simple_tag
def get_event_description(
    event: TimelineEvent,
    plugin_lookup: dict,
    request: Optional[HttpRequest] = None,
) -> str:
    """Return printable version of event description"""
    return timeline.get_event_description(event, plugin_lookup, request)


@register.simple_tag
def get_details_events(
    project: Project, view_classified: bool = False
) -> QuerySet:
    """Return recent events for card on project details page"""
    c_kwargs = {'classified': False} if not view_classified else {}
    return TimelineEvent.objects.filter(project=project, **c_kwargs).order_by(
        '-pk'
    )[:5]


@register.simple_tag
def get_plugin_lookup() -> dict:
    """Return lookup dict of app plugins with app name as key"""
    ret = {}
    for p in Plugin.objects.all():
        try:
            ret[p.name] = p.get_plugin()
        except Exception as ex:
            logger.error(f'Unable to retrieve plugin "{p.name}": {ex}')
    return ret


# Template rendering -----------------------------------------------------------


@register.simple_tag
def get_app_icon_html(event: TimelineEvent, plugin_lookup: dict) -> str:
    """Return icon link HTML for app by plugin lookup"""
    url = None
    title = event.app
    icon = ICON_UNKNOWN_APP  # Default in case the plugin is not found

    if event.app == 'projectroles':
        if event.project:
            url = reverse(
                'projectroles:detail',
                kwargs={'project': event.project.sodar_uuid},
            )
        title = 'Projectroles'
        icon = ICON_PROJECTROLES
    else:
        plugin_name = event.plugin if event.plugin else event.app
        if plugin_name in plugin_lookup.keys():
            url_kwargs = {}
            plugin = plugin_lookup[plugin_name]
            if isinstance(plugin, ProjectAppPluginPoint):
                url_kwargs['project'] = event.project.sodar_uuid
            entry_point = getattr(plugin, 'entry_point_url_id', None)
            if entry_point:
                try:
                    url = reverse(entry_point, kwargs=url_kwargs)
                except Exception as ex:
                    url = None
                    logger.error(
                        f'Unable to get URL for entry point "{entry_point}": '
                        f'{ex}'
                    )
            title = plugin.title
            if getattr(plugin, 'icon', None):
                icon = plugin.icon

    return (
        '<a {} class="sodar-tl-item-app-icon" title="{}" data-toggle="tooltip" '
        'data-placement="top">'
        '<i class="iconify" data-icon="{}"></i></a>'.format(
            'href="{}"'.format(url) if url else '', title, icon
        )
    )


@register.simple_tag
def get_status_style(status: str) -> str:
    """Retrn status style class"""
    return (
        (STATUS_STYLES[status.status_type] + ' text-light')
        if status.status_type in STATUS_STYLES
        else 'bg-light'
    )
