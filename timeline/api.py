"""API for the timeline app, used by other apps to add and update events"""

import re

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import Truncator

# Projectroles dependency
from projectroles.models import Project
from projectroles.plugins import ProjectAppPluginPoint
from projectroles.templatetags.projectroles_common_tags import get_user_html
from projectroles.utils import get_app_names

from timeline.models import ProjectEvent, ProjectEventObjectRef, \
    EVENT_STATUS_TYPES


# Local variables
APP_NAMES = get_app_names()
LABEL_MAX_WIDTH = 32

# Access Django user model
User = get_user_model()


class TimelineAPI:
    """Timeline API to be used by Django apps"""

    @staticmethod
    def add_event(
            project, app_name, user, event_name, description,
            classified=False, extra_data=None, status_type=None,
            status_desc=None, status_extra_data=None):
        """
        Create and save a ProjectEvent
        :param project: Project object
        :param app_name: ID string of app from which event was invoked (NOTE:
                         should correspond to member "name" in app plugin!)
        :param user: User invoking the event
        :param event_name: Event ID string (must match schema)
        :param description: Description of status change (may include {object
            label} references)
        :param classified: Whether event is classified (boolean, optional)
        :param extra_data: Additional event data (dict, optional)
        :param status_type: Initial status type (string, optional)
        :param status_desc: Initial status description (string, optional)
        :param status_extra_data: Extra data for initial status (dict, optional)
        :return: ProjectEvent object
        :raise: ValueError if app_name or status_type is invalid
        """
        if app_name not in APP_NAMES:
            raise ValueError('Unknown app name (active apps: {})'.format(
                ', '.join(x for x in APP_NAMES)))

        if status_type and status_type not in EVENT_STATUS_TYPES:
            raise ValueError('Unknown status type (valid types: {})'.format(
                ', '.join(x for x in EVENT_STATUS_TYPES)))

        event = ProjectEvent()
        event.project = project
        event.app = app_name
        event.user = user
        event.event_name = event_name
        event.description = description
        event.classified = classified

        if extra_data:
            event.extra_data = extra_data

        event.save()

        # Always add "INIT" status when creating, except for "INFO"
        if status_type != 'INFO':
            event.set_status('INIT')

        # Add additional status if set (use if e.g. event is immediately "OK")
        if status_type:
            event.set_status(status_type, status_desc, status_extra_data)

        return event

    @staticmethod
    def get_project_events(project, classified=False):
        """
        Return ProjectEvent objects for project
        :param project: Project object
        :param classified: Include classified
        :return: QuerySet
        """
        events = ProjectEvent.objects.filter(project=project)

        if not classified:
            events = events.filter(classified=False)

        return events

    @staticmethod
    def get_event_description(event, request=None):
        """Return printable version of event description"""
        desc = event.description
        unknown_label = '(unknown)'
        not_found_label = '<span class="text-danger">{}</span> {}'

        ref_ids = re.findall("{'?(.*?)'?\}", desc)

        if len(ref_ids) == 0:
            return event.description

        refs = {}

        def get_label(label):
            """Format label to be displayed"""
            if not {' ', '-'}.intersection(label):
                return Truncator(label).chars(LABEL_MAX_WIDTH)
            return label

        # TODO: Spaghetti much? Refactor
        for r in ref_ids:
            try:
                ref_obj = ProjectEventObjectRef.objects.get(
                    event=event,
                    label=r)

                # Get history link
                history_url = reverse('timeline:object_timeline', kwargs={
                    'project': event.project.omics_uuid,
                    'object_model': ref_obj.object_model,
                    'object_uuid': ref_obj.object_uuid})
                history_link = '<a href="{}" class="omics-tl-object-link">' \
                               '<i class="fa fa-clock-o"></i></a>'.format(
                                history_url)

                # Special case: User model
                if ref_obj.object_model == 'User':
                    try:
                        user = User.objects.get(omics_uuid=ref_obj.object_uuid)
                        refs[r] = '{} {}'.format(
                            get_user_html(user), history_link)

                    except User.DoesNotExist:
                        refs[r] = unknown_label

                # Special case: Project model
                elif ref_obj.object_model == 'Project':
                    try:
                        project = Project.objects.get(
                            omics_uuid=ref_obj.object_uuid)

                        if request and request.user.has_perm(
                                'projectroles.view_project', project):
                            refs[r] = '<a href="{}">{}</a>'.format(
                                reverse(
                                    'projetroles:detail',
                                    kwargs={'project': project.omics_uuid}),
                                get_label(project.title))

                        else:
                            refs[r] = '<span class="text-danger">' \
                                      '{}</span>'.format(
                                get_label(project.title))

                    except Project.DoesNotExist:
                        refs[r] = ref_obj.name

                # Special case: projectroles app
                elif event.app == 'projectroles':
                    refs[r] = not_found_label.format(
                        get_label(ref_obj.name), history_link)

                # Apps with plugins
                else:
                    app_plugin = ProjectAppPluginPoint.get_plugin(
                        name=event.app)

                    link_data = app_plugin.get_object_link(
                        ref_obj.object_model, ref_obj.object_uuid)

                    if link_data:
                        refs[r] = '<a href="{}" {}>{}</a> {}'.format(
                            link_data['url'],
                            ('target="_blank"'
                             if 'blank' in link_data and
                                link_data['blank'] is True else ''),
                            get_label(link_data['label']),
                            history_link)

                    else:
                        refs[r] = not_found_label.format(
                            get_label(ref_obj.name), history_link)

            except ProjectEventObjectRef.DoesNotExist:
                refs[r] = unknown_label

        return event.description.format(**refs)

    @staticmethod
    def get_object_url(project_uuid, obj):
        """
        Return URL for object history in timeline
        :param project_uuid: UUID of the related project
        :param obj: Django postgres database object
        :return: String
        """
        return reverse('timeline:object_timeline', kwargs={
            'project': project_uuid,
            'object_model': obj.__class__.__name__,
            'object_uuid': obj.omics_uuid})

    @staticmethod
    def get_object_link(project_uuid, obj):
        """
        Return inline HTML icon link for object history in timeline.
        :param project_uuid: UUID of the related project
        :param obj: Django postgres database object
        :return: String
        """
        return '<a href="{}" class="omics-tl-object-link">' \
               '<i class="fa fa-clock-o"></i></a>'.format(
                TimelineAPI.get_object_url(project_uuid, obj))
