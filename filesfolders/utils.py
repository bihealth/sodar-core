"""Utility functions for the filesfolders app"""

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.template.defaultfilters import filesizeformat
from django.urls import reverse

from projectroles.app_settings import AppSettingAPI

from filesfolders.models import File, BaseFilesfoldersClass
from filesfolders.templatetags.filesfolders_tags import get_flag


User = get_user_model()


def build_public_url(file: File, request: HttpRequest) -> str:
    """
    Return public URL for a file.

    :param file: File object for which public URL will be created
    :param request: HTTP request of View calling the function
    :return: URL (string)
    """
    return request.build_absolute_uri(
        reverse(
            'filesfolders:file_serve_public',
            kwargs={'secret': file.secret, 'file_name': file.name},
        )
    )


def extract_properties(
    item: BaseFilesfoldersClass, user: User, app_settings: AppSettingAPI
) -> tuple[str, str, str, str]:
    """
    Return a tuple of values used in search results.

    :param item: A File, Folder, or Hyperlink object
    :param user: User who initiated the search
    :param app_settings: App setting API object
    :return: Tuple of strings
    """
    item_class = item.__class__.__name__
    if item_class == 'HyperLink':
        name_url = item.url
    elif item_class == 'Folder':
        name_url = reverse(
            'filesfolders:list', kwargs={'folder': item.sodar_uuid}
        )
    elif item_class == 'File':
        name_url = reverse(
            'filesfolders:file_serve',
            kwargs={'file': item.sodar_uuid, 'file_name': item.name},
        )
    else:
        raise ValueError(f'Unexpected filesfolders item class: {item_class}')
    item_name_html = f'<a href="{name_url}">{item.name}</a>'
    allow_public_links = app_settings.get(
        'filesfolders', 'allow_public_links', project=item.project
    )
    can_share_link = user.has_perm(
        'filesfolders.share_public_link', item.project
    )
    if (
        item_class == 'File'
        and item.public_url
        and allow_public_links
        and can_share_link
    ):
        share_url = reverse(
            'filesfolders:file_public_link',
            kwargs={'file': item.sodar_uuid},
        )
        item_name_html += (
            f' <a href="{share_url}" title="Public Link">'
            '<i class="iconify" data-icon="mdi:link-variant"></i></a>'
        )
    if item.flag:
        item_name_html += ' ' + get_flag(item.flag)
    if item.folder:
        project_url = reverse(
            'filesfolders:list',
            kwargs={'folder': item.folder.sodar_uuid},
        )
    else:
        project_url = reverse(
            'filesfolders:list',
            kwargs={'project': item.project.sodar_uuid},
        )
    if item_class == 'File':
        size = filesizeformat(item.file.file.size)
    else:
        size = ''
    return (
        item_name_html,
        item_class,
        project_url,
        size,
    )
