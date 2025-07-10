"""Ajax API views for the timeline app"""

import html

from typing import Any, Optional

from django.http import HttpRequest, HttpResponseForbidden
from django.utils.timezone import localtime
from django.urls import reverse

from rest_framework.response import Response

# Projectroles dependency
from projectroles.views_ajax import (
    SODARBaseProjectAjaxView,
    SODARBasePermissionAjaxView,
    SODARBaseAjaxView,
)

from timeline.models import TimelineEvent, TimelineEventStatus
from timeline.templatetags.timeline_tags import get_status_style


class EventDetailMixin:
    """Mixin for event detail retrieval helpers"""

    @classmethod
    def get_status_extra_url(
        cls, status: TimelineEventStatus, request: HttpRequest
    ) -> Optional[str]:
        """Return URL for extra status data"""
        if status.extra_data == {} or not request.user.has_perm(
            'timeline.view_event_extra_data', status.event.project
        ):
            return None
        return reverse(
            'timeline:ajax_extra_status',
            kwargs={'eventstatus': status.sodar_uuid},
        )

    def get_event_details(
        self, event: TimelineEvent, request: HttpRequest
    ) -> dict:
        """
        Return event details.

        :param event: TimelineEvent object
        :param request: HttpRequest object
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
        for idx, s in enumerate(status_changes):
            ret['status'].append(
                {
                    'timestamp': localtime(s.timestamp).strftime(
                        '%Y-%m-%d %H:%M:%S'
                    ),
                    'description': s.description,
                    'type': s.status_type,
                    'class': get_status_style(s),
                    'extra_status_link': self.get_status_extra_url(s, request),
                }
            )
        return ret


class EventExtraDataMixin:
    """Mixin for event extra data retrieval helpers"""

    def _json_to_html(self, obj_json: Any) -> str:
        """Return HTML representation of JSON object"""
        str_list = []
        self._html_print_obj(obj_json, str_list, 0)
        str_list.append(
            '<button class="btn btn-secondary sodar-list-btn sodar-copy-btn '
            'sodar-tl-copy-btn" '
            'data-clipboard-target="#data-to-clipboard" '
            'title="Copy to clipboard" data-toggle="tooltip">'
            '<i class="iconify" data-icon="mdi:clipboard-multiple-outline"></i>'
            '</button>'
        )
        return ''.join(str_list)

    def _html_print_obj(self, obj_json: Any, str_list: list, indent: int):
        """Print JSON object to HTML string list"""
        if isinstance(obj_json, dict):
            self._html_print_dict(obj_json, str_list, indent)
        elif isinstance(obj_json, list):
            self._html_print_array(obj_json, str_list, indent)
        elif isinstance(obj_json, str):
            str_list.append('&quot;')
            str_list.append(html.escape(obj_json))
            str_list.append('&quot;')
        elif isinstance(obj_json, int):
            str_list.append(str(obj_json))
        elif isinstance(obj_json, bool):
            str_list.append(str(obj_json))
        elif obj_json is None:
            str_list.append('null')

    def _html_print_dict(self, html_dict: dict, str_list, indent: int):
        """Print JSON dict to HTML string list"""
        str_list.append('<span class="json-open-bracket">{</span><br>')
        str_list.append(
            '<span class="json-collapse-1" style="display: inline;">'
        )
        indent += 1
        for key, value in html_dict.items():
            str_list.append('<span class="json-indent">')
            str_list.append('&nbsp;&nbsp;' * indent)
            str_list.append('</span>')
            str_list.append('<span class="json-property">')
            str_list.append(html.escape(str(key)))
            str_list.append('</span>')
            str_list.append('<span class="json-semi-colon">: </span>')
            str_list.append('<span class="json-value">')
            self._html_print_obj(value, str_list, indent)
            str_list.append('</span>')
            str_list.append('<span class="json-comma">,</span><br>')
        if len(html_dict) > 0:
            del str_list[-1]
            str_list.append('<br>')
        str_list.append('</span>')
        str_list.append('&nbsp;&nbsp;' * (indent - 1))
        str_list.append('<span class="json-close-bracket">}</span>')

    def _html_print_array(self, array: list, str_list: list, indent: int):
        """Print JSON array to HTML string list"""
        str_list.append('<span class="json-open-bracket">[</span><br>')
        str_list.append(
            '<span class="json-collapse-1" style="display: inline;">'
        )
        indent += 1
        for value in array:
            str_list.append('<span class="json-indent">')
            str_list.append('&nbsp;&nbsp;' * indent)
            str_list.append('</span>')
            str_list.append('<span class="json-value">')
            self._html_print_obj(value, str_list, indent)
            str_list.append('</span>')
            str_list.append('<span class="json-comma">,</span><br>')
        if len(array) > 0:
            del str_list[-1]
            str_list.append('<br>')
        str_list.append('</span>')
        str_list.append('&nbsp;&nbsp;' * (indent - 1))
        str_list.append('<span class="json-close-bracket">]</span>')

    def get_event_extra(
        self, event: TimelineEvent, status: Optional[TimelineEventStatus] = None
    ) -> dict:
        """
        Return event extra data.

        :param event: TimelineEvent object
        :param status: TimelineEventStatus object
        :return: JSON-serializable dict
        """
        extra = status.extra_data if status else event.extra_data
        extra_data = self._json_to_html(extra)
        ret = {
            'app': event.app,
            'name': event.event_name,
            'user': event.user.username if event.user else 'N/A',
            'timestamp': localtime(event.get_timestamp()).strftime(
                '%Y-%m-%d %H:%M:%S'
            ),
            'extra': extra_data,
        }
        return ret


class ProjectEventDetailAjaxView(EventDetailMixin, SODARBaseProjectAjaxView):
    """Ajax view for retrieving event details for projects"""

    permission_required = 'timeline.view_timeline'

    def get(self, request, *args, **kwargs):
        event = TimelineEvent.objects.filter(
            sodar_uuid=self.kwargs['timelineevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_event', event.project
        ):
            return HttpResponseForbidden()
        return Response(self.get_event_details(event, request), status=200)


class ProjectEventExtraAjaxView(EventExtraDataMixin, SODARBaseProjectAjaxView):
    """Ajax view for retrieving event extra data for projects"""

    permission_required = 'timeline.view_event_extra_data'

    def get(self, request, *args, **kwargs):
        event = TimelineEvent.objects.filter(
            sodar_uuid=self.kwargs['timelineevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_event', event.project
        ):
            return HttpResponseForbidden()
        return Response(self.get_event_extra(event), status=200)


class SiteEventDetailAjaxView(EventDetailMixin, SODARBasePermissionAjaxView):
    """Ajax view for retrieving event details for site-wide events"""

    permission_required = 'timeline.view_site_timeline'

    def get(self, request, *args, **kwargs):
        event = TimelineEvent.objects.filter(
            sodar_uuid=self.kwargs['timelineevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_site_event'
        ):
            return HttpResponseForbidden()
        return Response(self.get_event_details(event, request), status=200)


class SiteEventExtraAjaxView(EventExtraDataMixin, SODARBasePermissionAjaxView):
    """Ajax view for retrieving event extra data for site-wide events"""

    permission_required = 'timeline.view_event_extra_data'

    def get(self, request, *args, **kwargs):
        event = TimelineEvent.objects.filter(
            sodar_uuid=self.kwargs['timelineevent']
        ).first()
        if event.classified and not request.user.has_perm(
            'timeline.view_classified_site_event'
        ):
            return HttpResponseForbidden()
        return Response(self.get_event_extra(event), status=200)


class EventStatusExtraAjaxView(EventExtraDataMixin, SODARBaseAjaxView):
    """Ajax view for retrieving event status extra data for events"""

    def get(self, request, *args, **kwargs):
        status = TimelineEventStatus.objects.filter(
            sodar_uuid=self.kwargs['eventstatus']
        ).first()
        event = status.event
        if event.classified and event.project:
            perm = 'view_classified_event'
        elif event.classified:
            perm = 'view_classified_site_event'
        else:
            perm = 'view_event_extra_data'
        project = getattr(event, 'project', None)
        if not request.user.has_perm('timeline.' + perm, project):
            return HttpResponseForbidden()
        return Response(self.get_event_extra(status.event, status), status=200)
