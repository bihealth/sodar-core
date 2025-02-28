"""Timeline API for adding and updating events"""

import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import Truncator

# Projectroles dependency
from projectroles.models import Project, RemoteSite
from projectroles.plugins import get_app_plugin
from projectroles.templatetags.projectroles_common_tags import get_user_html
from projectroles.utils import get_app_names

from timeline.models import (
    TimelineEvent,
    TimelineEventObjectRef,
    EVENT_STATUS_TYPES,
    OBJ_REF_UNNAMED,
    TL_STATUS_OK,
    TL_STATUS_INIT,
    TL_STATUS_SUBMIT,
    TL_STATUS_FAILED,
    TL_STATUS_INFO,
    TL_STATUS_CANCEL,
)


logger = logging.getLogger(__name__)
User = get_user_model()


# Local variables
APP_NAMES = get_app_names()
LABEL_MAX_WIDTH = 32
UNKNOWN_LABEL = '(unknown)'
PLUGIN_NOT_FOUND_MSG = 'Plugin not found: {plugin_name}'


class TimelineAPI:
    """Timeline backend API to be used by Django apps."""

    # Attributes --------------------------------------------------------------

    TL_STATUS_OK = TL_STATUS_OK
    TL_STATUS_INIT = TL_STATUS_INIT
    TL_STATUS_SUBMIT = TL_STATUS_SUBMIT
    TL_STATUS_FAILED = TL_STATUS_FAILED
    TL_STATUS_INFO = TL_STATUS_INFO
    TL_STATUS_CANCEL = TL_STATUS_CANCEL

    # Internal Helpers ---------------------------------------------------------

    @classmethod
    def _get_ref_label(cls, label):
        """Return reference object name in displayable form"""
        if not label:
            return OBJ_REF_UNNAMED
        if not {' ', '-'}.intersection(label):
            return Truncator(label).chars(LABEL_MAX_WIDTH)
        return label

    @classmethod
    def _get_history_link(cls, obj_ref):
        """Return history link HTML for event object reference"""
        url_name = 'timeline:list_object_site'
        url_kwargs = {
            'object_model': obj_ref.object_model,
            'object_uuid': obj_ref.object_uuid,
        }
        if obj_ref.event.project:
            url_name = 'timeline:list_object'
            url_kwargs['project'] = obj_ref.event.project.sodar_uuid
        history_url = reverse(url_name, kwargs=url_kwargs)
        return (
            '<a href="{}" class="sodar-tl-object-link">'
            '<i class="iconify" '
            'data-icon="mdi:clock-time-eight-outline"></i></a>'.format(
                history_url
            )
        )

    @classmethod
    def _get_not_found_label(cls, obj_ref):
        """Get label for object which is not found in the database"""
        return '<span class="text-danger">{}</span> {}'.format(
            cls._get_ref_label(obj_ref.name), cls._get_history_link(obj_ref)
        )

    @classmethod
    def _get_project_desc(cls, obj_ref, request=None):
        """Get description HTML for special case: Project model"""
        project = Project.objects.filter(sodar_uuid=obj_ref.object_uuid).first()
        if (
            project
            and request
            and request.user.has_perm('projectroles.view_project', project)
        ):
            return '<a class="sodar-tl-project-link" href="{}">{}</a>'.format(
                reverse(
                    'projectroles:detail',
                    kwargs={'project': project.sodar_uuid},
                ),
                cls._get_ref_label(project.title),
            )
        elif project:
            return '<span class="text-danger">{}</span>'.format(
                cls._get_ref_label(project.title)
            )
        return obj_ref.name

    @classmethod
    def _get_remote_site_desc(cls, obj_ref, request=None):
        """Get description HTML for special case: RemoteSite model"""
        site = RemoteSite.objects.filter(sodar_uuid=obj_ref.object_uuid).first()
        if site and request and request.user.is_superuser:
            return '<a href="{}">{}</a> {}'.format(
                reverse(
                    'projectroles:remote_projects',
                    kwargs={'remotesite': site.sodar_uuid},
                ),
                site.name,
                cls._get_history_link(obj_ref),
            )
        elif site:
            return site.name
        return cls._get_not_found_label(obj_ref)

    @classmethod
    def _get_ref_description(cls, event, ref_label, app_plugin, request):
        """
        Get reference object description for event description, or unknown label
        if not found.

        :param event: TimelineEvent object
        :param ref_label: Label for the reference object (string)
        :param app_plugin: App plugin or None
        :param request: Request object or None
        :return: String (contains HTML)
        """
        # Special case: Extra data reference
        if ref_label.startswith('extra-'):
            desc = app_plugin.get_extra_data_link(event.extra_data, ref_label)
            return desc if desc else UNKNOWN_LABEL

        # Get object reference
        try:
            obj_ref = TimelineEventObjectRef.objects.get(
                event=event, label=ref_label
            )
        except TimelineEventObjectRef.DoesNotExist:
            return UNKNOWN_LABEL

        # Special case: User model
        if obj_ref.object_model == 'User':
            try:
                user = User.objects.get(sodar_uuid=obj_ref.object_uuid)
                return '{} {}'.format(
                    get_user_html(user), cls._get_history_link(obj_ref)
                )
            except User.DoesNotExist:
                return UNKNOWN_LABEL

        # Special case: Project model
        elif obj_ref.object_model == 'Project':
            return cls._get_project_desc(obj_ref, request)

        # Special case: RemoteSite model
        elif obj_ref.object_model == 'RemoteSite':
            return cls._get_remote_site_desc(obj_ref, request)

        # Special case: projectroles app
        elif event.app == 'projectroles':
            return cls._get_not_found_label(obj_ref)

        # Apps with plugins
        else:
            try:
                link = app_plugin.get_object_link(
                    obj_ref.object_model, obj_ref.object_uuid
                )
            except Exception as ex:
                logger.error(
                    'Exception in {}.get_object_link(): {}'.format(
                        app_plugin.name, ex
                    )
                )
                if settings.DEBUG:
                    raise ex
                link = None
            if link:
                if not link.name:
                    logger.warning(
                        'Empty name returned by plugin "{}" for object '
                        'reference "{}" ({})"'.format(
                            app_plugin.name, obj_ref, obj_ref.object_uuid
                        )
                    )
                return '<a href="{}" {}>{}</a> {}'.format(
                    link.url,
                    'target="_blank"' if link.blank else '',
                    cls._get_ref_label(link.name),
                    cls._get_history_link(obj_ref),
                )
            else:
                return cls._get_not_found_label(obj_ref)

    # API functions ------------------------------------------------------------

    @classmethod
    def add_event(
        cls,
        project,
        app_name,
        user,
        event_name,
        description,
        classified=False,
        extra_data=None,
        status_type=None,
        status_desc=None,
        status_extra_data=None,
        plugin_name=None,
    ):
        """
        Create and save a timeline event.

        :param project: Project object or None
        :param app_name: Name of app from which event was invoked (must
            correspond to "name" attribute of app plugin)
        :param user: User invoking the event or None
        :param event_name: Event ID string (must match schema)
        :param description: Description of status change (may include {object
            label} references)
        :param classified: Whether event is classified (boolean, optional)
        :param extra_data: Additional event data (dict, optional)
        :param status_type: Initial status type (string, optional)
        :param status_desc: Initial status description (string, optional)
        :param status_extra_data: Extra data for initial status (dict, optional)
        :param plugin_name: Name of plugin to which the event is related
            (optional, plugin with the name of the app is assumed if unset)
        :return: TimelineEvent object
        :raise: ValueError if app_name or status_type is invalid
        """
        if app_name not in APP_NAMES:
            raise ValueError(
                'Unknown app name "{}" (active apps: {})'.format(
                    app_name, ', '.join(x for x in APP_NAMES)
                )
            )
        if status_type and status_type not in EVENT_STATUS_TYPES:
            raise ValueError(
                'Unknown status type "{}" (valid types: {})'.format(
                    status_type, ', '.join(x for x in EVENT_STATUS_TYPES)
                )
            )

        # Handle user in case called with AnonymousUser object
        if user and user.is_anonymous:
            user = None

        event = TimelineEvent()
        event.project = project
        event.app = app_name
        event.plugin = plugin_name
        event.user = user
        event.event_name = event_name
        event.description = description
        event.classified = classified
        if extra_data:
            event.extra_data = extra_data
        event.save()

        # Always add "INIT" status when creating, except for "INFO"
        if status_type not in [TL_STATUS_INFO, TL_STATUS_INIT]:
            event.set_status(TL_STATUS_INIT)
        # Add additional status if set (use if e.g. event is immediately "OK")
        if status_type:
            event.set_status(status_type, status_desc, status_extra_data)
        return event

    @classmethod
    def get_project_events(cls, project, classified=False):
        """
        Return timeline events for a project.

        :param project: Project object
        :param classified: Include classified (boolean)
        :return: QuerySet
        """
        events = TimelineEvent.objects.filter(project=project)
        if not classified:
            events = events.filter(classified=False)
        return events

    @classmethod
    def get_event_description(cls, event, plugin_lookup=None, request=None):
        """
        Return the description of a timeline event as HTML.

        :param event: TimelineEvent object
        :param plugin_lookup: App plugin lookup dict (optional)
        :param request: Request object (optional)
        :return: String (contains HTML)
        """
        desc = event.description
        ref_ids = re.findall('{\'?(.*?)\'?}', desc)
        if len(ref_ids) == 0:
            return event.description
        refs = {}
        app_plugin = None

        if event.app != 'projectroles':
            plugin_name = event.plugin if event.plugin else event.app
            if plugin_lookup:
                app_plugin = plugin_lookup.get(plugin_name)
            else:
                app_plugin = get_app_plugin(plugin_name)
            if not app_plugin:
                msg = PLUGIN_NOT_FOUND_MSG.format(plugin_name=plugin_name)
                logger.error(msg + ' (UUID={})'.format(event.sodar_uuid))
                return (
                    '<span class="sodar-tl-plugin-error text-danger">'
                    '{}</span>'.format(msg)
                )

        # Get links for object references
        for r in ref_ids:
            refs[r] = cls._get_ref_description(event, r, app_plugin, request)
        try:
            return event.description.format(**refs)
        except Exception as ex:  # Dispaly exception instead of crashing
            logger.error(
                'Error formatting event description: {} (UUID={})'.format(
                    ex, event.sodar_uuid
                )
            )
            return (
                '<span class="sodar-tl-format-error text-danger">'
                '{}: {}</span>'.format(ex.__class__.__name__, ex)
            )

    @classmethod
    def get_object_url(cls, obj, project=None):
        """
        Return the URL for a timeline event object history.

        :param obj: Django database object
        :param project: Related Project object or None
        :return: String
        """
        url_name = 'timeline:list_object_site'
        url_kwargs = {
            'object_model': obj.__class__.__name__,
            'object_uuid': obj.sodar_uuid,
        }
        if project:
            url_name = 'timeline:list_object'
            url_kwargs['project'] = project.sodar_uuid
        return reverse(url_name, kwargs=url_kwargs)

    @classmethod
    def get_object_link(cls, obj, project=None):
        """
        Return an inline HTML icon link for a timeline event object history.

        :param obj: Django database object
        :param project: Related Project object or None
        :return: String (contains HTML)
        """
        return (
            '<a href="{}" class="sodar-tl-object-link">'
            '<i class="iconify" data-icon="mdi:clock-time-eight-outline"></i>'
            '</a>'.format(cls.get_object_url(obj, project))
        )

    @classmethod
    def get_models(cls):
        """
        Return timeline event model classes for custom/advanced queries.

        :return: TimelineEvent, TimelineEventObjectRef
        """
        return TimelineEvent, TimelineEventObjectRef
