"""Plugins for the Timeline app"""

import logging

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.urls import reverse

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS, Project
from projectroles.plugins import (
    ProjectAppPluginPoint,
    BackendPluginPoint,
    SiteAppPluginPoint,
    PluginSearchResult,
    PluginSearchResultCell,
)
from projectroles.utils import get_display_name

from timeline.api import TimelineAPI
from timeline.models import TimelineEvent
from timeline.urls import urls_ui_project, urls_ui_site, urls_ui_admin
from timeline.templatetags.timeline_tags import (
    ICON_PROJECTROLES,
    ICON_UNKNOWN_APP,
    get_timestamp,
    get_plugin_lookup,
    get_status_style,
    get_event_name,
)


User = get_user_model()
logger = logging.getLogger(__name__)


# Local constants
STATS_DESC_USER_COUNT = 'Amount of users who have initiated events'


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with Projectroles"""

    # Properties required by django-plugins ------------------------------

    #: Name (used as plugin ID)
    name = 'timeline'

    #: Title (used in templates)
    title = 'Timeline'

    #: UI URLs
    urls = urls_ui_project

    # Properties defined in ProjectAppPluginPoint -----------------------

    #: Iconify icon
    icon = 'mdi:clock-time-eight'

    #: Entry point URL ID (must take project sodar_uuid as "project" argument)
    entry_point_url_id = 'timeline:list_project'

    #: Description string
    description = 'Timeline of {} events'.format(
        get_display_name(SODAR_CONSTANTS['PROJECT_TYPE_PROJECT'])
    )

    #: Required permission for accessing the app
    app_permission = 'timeline.view_timeline'

    #: Enable or disable general search from project title bar
    search_enable = True

    #: List of search object types for the app
    search_types = ['timeline']

    #: Search results template
    search_template = 'timeline/_search_results.html'

    #: App card template for the project details page
    details_template = 'timeline/_details_card.html'

    #: App card title for the project details page
    details_title = 'Timeline Overview'

    #: Position in plugin ordering
    plugin_ordering = 40

    #: Display application for categories in addition to projects
    category_enable = True

    #: Names of plugin specific Django settings to display in siteinfo
    info_settings = ['TIMELINE_PAGINATION', 'TIMELINE_SEARCH_LIMIT']

    @classmethod
    def _check_permission(cls, user: User, event: TimelineEvent) -> bool:
        """Check if user has permission to view event"""
        if event.project and event.classified:
            return user.has_perm(
                'timeline.view_classified_event', event.project
            )
        elif event.project:
            return user.has_perm('timeline.view_timeline', event.project)
        elif event.classified:
            return user.has_perm('timeline.view_classified_site_event')
        return user.has_perm('timeline.view_site_timeline')

    def get_statistics(self) -> dict:
        return {
            'event_count': {
                'label': 'Events',
                'value': TimelineEvent.objects.all().count(),
            },
            'user_count': {
                'label': 'Users',
                'description': STATS_DESC_USER_COUNT,
                'value': TimelineEvent.objects.exclude(user__isnull=True)
                .values('user')
                .distinct()
                .count(),
            },
        }

    def search(
        self,
        search_terms: list[str],
        user: User,
        projects: QuerySet[Project],
        **kwargs: str,
    ) -> list[PluginSearchResult]:
        """
        Return app items based on one or more search terms, user, optional type
        and optional keywords.

        :param search_terms: Search terms to be joined with the OR operator
                             (list of strings)
        :param user: User object for user initiating the search
        :param projects: QuerySet of projects where the terms are searched
        :param kwargs: Search options as key/value pairs (optional)
        :return: List of PluginSearchResult objects
        """
        items = []
        if kwargs.get('type', 'timeline') == 'timeline':
            events = list(
                TimelineEvent.objects.find(search_terms, projects, kwargs)
            )
            items = [e for e in events if self._check_permission(user, e)]
        plugin_lookup = get_plugin_lookup()
        rows = []
        for item in items:
            app_badge_icon = ICON_UNKNOWN_APP
            app_badge_url = None
            app_badge_title = item.app  # Default in case the plugin is not found
            app_badge_text = get_event_name(item)
            if item.app == 'projectroles':
                if item.project:
                    app_badge_url = reverse(
                        'projectroles:detail',
                        kwargs={'project': item.project.sodar_uuid},
                    )
                app_badge_title = 'Projectroles'
                app_badge_icon = ICON_PROJECTROLES
            else:
                plugin_name = item.plugin if item.plugin else item.app
                if plugin_name in plugin_lookup.keys():
                    url_kwargs = {}
                    plugin = plugin_lookup[plugin_name]
                    if isinstance(plugin, ProjectAppPluginPoint):
                        url_kwargs['project'] = item.project.sodar_uuid
                    entry_point = getattr(plugin, 'entry_point_url_id', None)
                    if entry_point:
                        try:
                            app_badge_url = reverse(entry_point, kwargs=url_kwargs)
                        except Exception as ex:
                            app_badge_url = None
                            logger.error(
                                f'Unable to get URL for entry point "{entry_point}": '
                                f'{ex}'
                            )
                    app_badge_title = plugin.title
                    if getattr(plugin, 'icon', None):
                        app_badge_icon = plugin.icon
            rows.append(
                [
                    # Timestamp
                    PluginSearchResultCell(
                        value=get_timestamp(item),
                        cell_class='text-nowrap',
                    ),
                    # Description
                    # TODO: add badges
                    # {% if event.user %}
                    #   {% get_user_badge event.user 'mr-1' as user_badge %}
                    #   {{ user_badge | safe }}
                    # {% endif %}
                    # {% if event.project %}
                    #   {% get_project_badge event.project extra_class='mr-1' as project_badge %}
                    #   {{ project_badge | safe }}
                    # {% endif %}
                    PluginSearchResultCell(
                        # TODO: we should use timeline.templatetags.timeline_tags.get_event_description()
                        value=item.description,
                        badges=[
                            {'icon': app_badge_icon, 'url': app_badge_url, 'title': app_badge_title, 'text': app_badge_text},
                            # {'icon': user_badge_icon, 'url': user_badge_url, 'title': user_badge_title, 'text': user_badge_text},
                            # {'icon': project_badge_icon, 'url': project_badge_url, 'title': project_badge_title, 'text': project_badge_text},
                        ],
                        # icons=[
                        #     {
                        #         'icon': icon,
                        #         'url': icon_url,
                        #         'title': icon_title,
                        #     }
                        # ],
                        cell_class='sodar-overflow-container',
                        # highlight=search_terms, # XXX: not in the original
                    ),
                    # Status
                    PluginSearchResultCell(
                        value=item.get_status().status_type,
                        cell_class=f'{get_status_style(item.get_status())} text-light sodar-tl-item-status',
                    ),
                ]
            )
        ret = PluginSearchResult(
            category='all',
            title='Timeline Events',
            search_types=['timeline'],
            fields=['Timestamp', 'Description', 'Status'],
            rows=rows,
        )
        return [ret]


class BackendPlugin(BackendPluginPoint):
    """Plugin for registering backend app with Projectroles"""

    #: Name (used as plugin ID)
    name = 'timeline_backend'

    #: Title (used in templates)
    title = 'Timeline Backend'

    #: Iconify icon
    icon = 'mdi:clock-time-eight-outline'

    #: Description string
    description = 'Timeline backend for modifying events'

    def get_api(self, **kwargs) -> TimelineAPI:
        """Return API entry point object."""
        return TimelineAPI()


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'timeline_site'

    #: Title (used in templates)
    title = 'Site-Wide Events'

    #: UI URLs
    urls = urls_ui_site

    #: Iconify icon
    icon = 'mdi:clock-time-eight-outline'

    #: Description string
    description = 'Timeline of Site-Wide Events'

    #: Entry point URL ID
    entry_point_url_id = 'timeline:list_site'

    #: Required permission for displaying the app
    app_permission = 'timeline.view_site_timeline'


class AdminSiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (used as plugin ID)
    name = 'timeline_site_admin'

    #: Title (used in templates)
    title = 'All Timeline Events'

    #: UI URLs
    urls = urls_ui_admin

    #: Iconify icon
    # icon = 'mdi:clock-star-four-points-outline'
    icon = 'mdi:web-clock'

    #: Description string
    description = 'Admin view for all timeline events on the site'

    #: Entry point URL ID
    entry_point_url_id = 'timeline:list_admin'

    #: Required permission for displaying the app
    app_permission = 'timeline.view_site_admin'
