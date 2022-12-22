"""Ajax API views for the timeline app"""

from django.utils.timezone import localtime

from rest_framework.response import Response

from json2html import *
from jinja2 import *

# Projectroles dependency
from projectroles.views_ajax import (
    SODARBaseProjectAjaxView,
    SODARBasePermissionAjaxView,
)

from timeline.models import ProjectEvent
from timeline.templatetags.timeline_tags import get_status_style
from timeline.templatetags.timeline_tags import get_event_extra_data, collect_extra_data


class EventDetailMixin:
    """Mixin for event detail retrieval helpers"""

    def get_event_details(self, event):
        """
        Return event details.

        :param event: ProjectEvent object
        :return: Dict
        """
        ret = {
            'app': event.app,
            'name': event.event_name,
            'user': event.user.username if event.user else 'N/A',
            'timestamp': localtime(event.get_timestamp()).strftime(
                '%Y-%m-%d %H:%M:%S'
            ),
            'status': [],
        }
        status_changes = event.get_status_changes(reverse=True)
        for s in status_changes:
            ret['status'].append(
                {
                    'timestamp': localtime(s.timestamp).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    'description': s.description,
                    'type': s.status_type,
                    'class': get_status_style(s),
                }
            )
        return ret


class EventExtraMixin:
    """Mixin for event extra data retrieval helpers"""

    def form_html(self, event):
        """
        Return event extra data as html suitable exactly for jquery.
        :param event: ProjectEvent object
        :return: HTML string
        """
        extra_list = []
        event_extra_data_list = collect_extra_data(event)
        for data in event_extra_data_list:
            data0 = data[0]
            data2pk = data[2].pk
            extra = get_event_extra_data(data[2])
            extra_list.append((data0, data2pk, extra))

        template = Template("""
        <div class="modal-body tab-content">
        {% for data in extra_list %}
          <div class="tab-pane" role="tabpanel" id="{{ data.0 }}-{{ data.1 }}">
            <pre id="{{ data.0 }}-pre-{{ data.1 }}">{% autoescape off %}{{ data.2 }}{% endautoescape %}</pre>
            <button class="btn btn-secondary sodar-list-btn sodar-copy-btn sodar-tl-copy-btn"
                    data-clipboard-target="#{{ data.0 }}-pre-{{ data.1 }}"
                    title="Copy to clipboard" data-toggle="tooltip">
              <i class="iconify" data-icon="mdi:clipboard-multiple-outline"></i>
            </button>
          </div>
        {% endfor %}
      </div>
        """)
        html_doc = template.render(extra_list=extra_list)
        return html_doc

    def get_event_extra(self, event):
        """
        Return event extra data.
        :param event: ProjectEvent object
        :return: JSON-serializable dict
        """
        extra_data_html = self.form_html(event)
        ret = {
            'app': event.app,
            'user': event.user.username if event.user else 'N/A',
            'extra': " ".join(extra_data_html.split()),
        }
        return ret


class ProjectEventDetailAjaxView(EventDetailMixin, SODARBaseProjectAjaxView):
    """Ajax view for retrieving event details for projects"""

    permission_required = 'timeline.view_timeline'
    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        event = ProjectEvent.objects.filter(
            sodar_uuid=self.kwargs['projectevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_event', event.project
        ):
            return Response(status=403)
        return Response(self.get_event_details(event), status=200)


class ProjectEventExtraAjaxView(EventExtraMixin, SODARBaseProjectAjaxView):
    """Ajax view for retrieving event extra data for projects"""

    permission_required = 'timeline.view_timeline'
    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        event = ProjectEvent.objects.filter(
            sodar_uuid=self.kwargs['projectevent']
        ).first()
        if (
            not bool(event.extra_data)
            or event.classified
            and not request.user.has_perm(
                'timeline.view_classified_event', event.project
            )
        ):
            return Response(status=403)
        return Response(self.get_event_extra(event), status=200)


class SiteEventDetailAjaxView(EventDetailMixin, SODARBasePermissionAjaxView):
    """Ajax view for retrieving event details for site-wide events"""

    permission_required = 'timeline.view_site_timeline'
    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        event = ProjectEvent.objects.filter(
            sodar_uuid=self.kwargs['projectevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_site_event'
        ):
            return Response(status=403)
        return Response(self.get_event_details(event), status=200)


class SiteEventExtraAjaxView(EventExtraMixin, SODARBasePermissionAjaxView):
    """Ajax view for retrieving event extra data for site-wide events"""

    permission_required = 'timeline.view_site_timeline'
    allow_anonymous = True

    def get(self, request, *args, **kwargs):
        event = ProjectEvent.objects.filter(
            sodar_uuid=self.kwargs['projectevent']
        ).first()
        if (
            not bool(event.extra_data)
            or event.classified
            and not request.user.has_perm('timeline.view_classified_site_event')
        ):
            return Response(status=403)
        return Response(self.get_event_extra(event), status=200)
