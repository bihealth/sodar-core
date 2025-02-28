from django.conf import settings
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import (
    ProjectAppPluginPoint,
    PluginAppSettingDef,
    PluginObjectLink,
    PluginSearchResult,
)

from filesfolders.models import File, Folder, HyperLink
from filesfolders.urls import urlpatterns


# SODAR constants
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_TYPE_BOOLEAN = SODAR_CONSTANTS['APP_SETTING_TYPE_BOOLEAN']

# Local constants
SHOW_LIST_COLUMNS = getattr(settings, 'FILESFOLDERS_SHOW_LIST_COLUMNS', False)


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (used as plugin ID)
    name = 'filesfolders'

    #: Title (used in templates)
    title = 'Files'

    #: UI URLs
    urls = urlpatterns

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: App setting definitions
    app_settings = [
        PluginAppSettingDef(
            name='allow_public_links',
            scope=APP_SETTING_SCOPE_PROJECT,
            type=APP_SETTING_TYPE_BOOLEAN,
            default=False,
            label='Allow public links',
            description='Allow generation of public links for files',
        )
    ]

    #: Iconify icon
    icon = 'mdi:file'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'filesfolders:list'

    #: Description string
    description = (
        'Smaller files (e.g., reports, spreadsheets, and presentations)'
    )

    #: Required permission for accessing the app
    app_permission = 'filesfolders.view_data'

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ['file', 'folder', 'link']

    #: Search results template
    search_template = 'filesfolders/_search_results.html'

    #: App card template for the project details page
    details_template = 'filesfolders/_details_card.html'

    #: App card title for the project details page
    details_title = 'Files Overview'

    #: Position in plugin ordering
    plugin_ordering = 30

    project_list_columns = {
        'files': {
            'title': 'Files',
            'width': 75,
            'description': 'files stored for the project',
            'active': SHOW_LIST_COLUMNS,
            'ordering': 35,
            'align': 'right',
        },
        'links': {
            'title': 'Links',
            'width': 75,
            'description': 'Hyperlinks defined in the files app',
            'active': SHOW_LIST_COLUMNS,
            'ordering': 25,
            'align': 'right',
        },
    }

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = [
        'FILESFOLDERS_LINK_BAD_REQUEST_MSG',
        'FILESFOLDERS_MAX_ARCHIVE_SIZE',
        'FILESFOLDERS_MAX_UPLOAD_SIZE',
        'FILESFOLDERS_SERVE_AS_ATTACHMENT',
        'FILESFOLDERS_SHOW_LIST_COLUMNS',
    ]

    def get_object_link(self, model_str, uuid):
        """
        Return URL referring to an object used by the app, along with a name to
        be shown to the user for linking.

        :param model_str: Object class (string)
        :param uuid: sodar_uuid of the referred object
        :return: PluginObjectLink or None if not found
        """
        obj = self.get_object(eval(model_str), uuid)
        if not obj:
            return None
        elif obj.__class__ == File:
            return PluginObjectLink(
                url=reverse(
                    'filesfolders:file_serve',
                    kwargs={'file': obj.sodar_uuid, 'file_name': obj.name},
                ),
                name=obj.name,
                blank=True,
            )
        elif obj.__class__ == Folder:
            return PluginObjectLink(
                url=reverse(
                    'filesfolders:list', kwargs={'folder': obj.sodar_uuid}
                ),
                name=obj.name,
            )
        elif obj.__class__ == HyperLink:
            return PluginObjectLink(url=obj.url, name=obj.name, blank=True)
        return None

    def search(self, search_terms, user, search_type=None, keywords=None):
        """
        Return app items based on one or more search terms, user, optional type
        and optional keywords.

        :param search_terms: Search terms to be joined with the OR operator
                             (list of strings)
        :param user: User object for user initiating the search
        :param search_type: String
        :param keywords: List (optional)
        :return: List of PluginSearchResult objects
        """
        items = []
        if not search_type:
            files = File.objects.find(search_terms, keywords)
            folders = Folder.objects.find(search_terms, keywords)
            links = HyperLink.objects.find(search_terms, keywords)
            items = list(files) + list(folders) + list(links)
            items.sort(key=lambda x: x.name.lower())
        elif search_type == 'file':
            items = File.objects.find(search_terms, keywords).order_by('name')
        elif search_type == 'folder':
            items = Folder.objects.find(search_terms, keywords).order_by('name')
        elif search_type == 'link':
            items = HyperLink.objects.find(search_terms, keywords).order_by(
                'name'
            )
        if items:
            items = [
                x
                for x in items
                if user.has_perm('filesfolders.view_data', x.project)
            ]
        ret = PluginSearchResult(
            category='all',
            title='Files, Folders and Links',
            search_types=['file', 'folder', 'link'],
            items=items,
        )
        return [ret]

    def get_statistics(self):
        return {
            'file_count': {
                'label': 'Files',
                'value': File.objects.all().count(),
            },
            'folder_count': {
                'label': 'Folders',
                'value': Folder.objects.all().count(),
            },
            'link_count': {
                'label': 'Hyperlinks',
                'value': HyperLink.objects.all().count(),
            },
        }

    def get_project_list_value(self, column_id, project, user):
        """
        Return a value for the optional additional project list column specific
        to a project.

        :param column_id: ID of the column (string)
        :param project: Project object
        :param user: User object (current user)
        :return: String (may contain HTML), integer or None
        """
        if column_id == 'files':
            count = File.objects.filter(project=project).count()
        elif column_id == 'links':
            count = HyperLink.objects.filter(project=project).count()
        if count > 0:
            return '<a href="{}">{}</a>'.format(
                reverse(
                    'filesfolders:list', kwargs={'project': project.sodar_uuid}
                ),
                count,
            )
        return 0
