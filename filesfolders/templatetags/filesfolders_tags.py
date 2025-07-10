"""Template tags for the filesfolders app"""

import logging

from typing import Any

from django import template
from django.conf import settings

# Projectroles dependency
from projectroles.app_settings import AppSettingAPI
from projectroles.models import Project

from filesfolders.models import File, HyperLink, FILESFOLDERS_FLAGS


app_settings = AppSettingAPI()
logger = logging.getLogger(__name__)
register = template.Library()


APP_NAME = 'filesfolders'


@register.filter
def get_class(obj: Any) -> str:
    return obj.__class__.__name__


@register.simple_tag
def get_details_items(project: Project) -> list:
    """Return recent files/links for card on project details page"""
    files = File.objects.filter(project=project).order_by('-date_modified')[:5]
    links = HyperLink.objects.filter(project=project).order_by(
        '-date_modified'
    )[:5]
    ret = list(files) + list(links)
    ret.sort(key=lambda x: x.date_modified, reverse=True)
    return ret[:5]


@register.simple_tag
def get_file_icon(file: File) -> str:
    """Return file icon"""
    ret = 'file-outline'
    try:
        mt = file.file.file.mimetype
    except Exception as ex:
        if settings.DEBUG:
            raise ex
        logger.error(
            f'Exception in accessing file data (UUID={file.sodar_uuid}): {ex}'
        )
        return ret
    if mt == 'application/pdf':
        ret = 'file-pdf-outline'
    elif (
        mt == 'application/vnd.openxmlformats-officedocument.'
        'presentationml.presentation'
    ):
        ret = 'file-powerpoint-outline'
    elif 'compressed' in mt or 'zip' in mt:
        ret = 'archive-outline'
    elif (
        'excel' in mt
        or mt == 'application/vnd.openxmlformats-'
        'officedocument.spreadsheetml.sheet'
    ):
        ret = 'file-excel-outline'
    elif 'image/' in mt:
        ret = 'file-image-outline'
    elif 'text/' in mt:
        ret = 'file-document-outline'
    # Default if not found
    return 'mdi:' + ret


@register.simple_tag
def get_flag(flag_name: str, tooltip: bool = True) -> str:
    """Return item flag HTML"""
    f = FILESFOLDERS_FLAGS[flag_name]
    tip_str = ''
    if tooltip:
        tip_str = (
            'title="{}" data-toggle="tooltip" '
            'data-placement="top"'.format(f['label'])
        )
    return (
        '<i class="iconify text-{} sodar-ff-flag-icon" data-icon="{}" {}>'
        '</i>'.format(f['color'], f['icon'], tip_str)
    )


@register.simple_tag
def get_flag_status(val: str, choice: str) -> str:
    """Return item flag status HTML for form"""
    if val == choice:
        return 'checked="checked"'
    return ''


@register.simple_tag
def get_flag_classes(flag_name: str) -> str:
    """Return CSS classes for item link based on flag name"""
    return FILESFOLDERS_FLAGS[flag_name]['text_classes']
