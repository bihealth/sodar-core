"""Plugins for the bgjobs app"""

from djangoplugins.point import PluginPoint

# Projectroles dependency
from projectroles.plugins import ProjectAppPluginPoint, SiteAppPluginPoint

from bgjobs.urls import urls_ui_project, urls_ui_site


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    #: Name (used as plugin ID)
    name = 'bgjobs'

    #: Title (used in templates)
    title = 'Background Jobs'

    #: UI URLs
    urls = urls_ui_project

    #: Iconify icon
    icon = 'mdi:server'

    entry_point_url_id = 'bgjobs:list'

    description = 'Jobs executed in the background'

    #: Required permission for accessing the app
    app_permission = 'bgjobs.view_data'

    #: Enable or disable general search from project title bar
    search_enable = False

    #: List of search object types for the app
    search_types = []

    #: Search results template
    search_template = None

    #: App card template for the project details page
    details_template = 'bgjobs/_details_card.html'

    #: App card title for the project details page
    details_title = 'Background Jobs App Overview'

    #: Position in plugin ordering
    plugin_ordering = 100

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = ['BGJOBS_PAGINATION']


class BackgroundJobsPluginPoint(PluginPoint):
    """
    Definition of a plugin point for registering background job types with the
    bgjobs app.
    """

    #: Mapping from job specialization name to specialization class
    # (OneToOneField "inheritance").
    job_specs = {}


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'bgjobs_site'

    #: Title (used in templates)
    title = 'Site Background Jobs'

    #: UI URLs
    urls = urls_ui_site

    #: Iconify icon
    icon = 'mdi:server'

    #: Description string
    description = 'Site-wide background jobs'

    #: Entry point URL ID
    entry_point_url_id = 'bgjobs:site_list'

    #: Required permission for displaying the app
    app_permission = 'bgjobs:bgjobs.site_view_data'
