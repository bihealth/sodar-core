"""Ajax API views for the timeline app"""
import html

from django.utils.timezone import localtime

from rest_framework.response import Response

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


class ExtraDataHTMLMixin:
    def json_to_html(cls, obj_json):
        str_list = []
        cls.html_print_obj(obj_json, str_list, 0)
        return ''.join(str_list)


    def html_print_obj(cls, obj_json, str_list: list, indent):
        if isinstance(obj_json, dict):
            cls.html_print_dict(obj_json, str_list, indent)
        elif isinstance(obj_json, list):
            cls.html_print_array(obj_json, str_list, indent)
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


    def html_print_dict(cls, dct: dict, str_list, indent):
        str_list.append('<span class="json-open-bracket">{</span>\n')
        str_list.append('<span class="json-collapse-1" style="display: inline;">')

        indent += 1
        for key, value in dct.items():
            str_list.append('<span class="json-indent">')
            str_list.append('  ' * indent)
            str_list.append('</span>')
            str_list.append('<span class="json-property">')

            str_list.append(html.escape(str(key)))

            str_list.append('</span>')
            str_list.append('<span class="json-semi-colon">: </span>')

            str_list.append('<span class="json-value">')
            cls.html_print_obj(value, str_list, indent)

            str_list.append('</span>')
            str_list.append('<span class="json-comma">,</span>\n')

        if len(dct) > 0:
            del str_list[-1]
            str_list.append('\n')

        str_list.append('</span>')
        str_list.append('  ' * (indent - 1))
        str_list.append('<span class="json-close-bracket">}</span>')


    def html_print_array(cls, array, str_list, indent):
        str_list.append('<span class="json-open-bracket">[</span>\n')
        str_list.append('<span class="json-collapse-1" style="display: inline;">')

        indent += 1
        for value in array:
            str_list.append('<span class="json-indent">')
            str_list.append('  ' * indent)
            str_list.append('</span>')
            str_list.append('<span class="json-value">')
            cls.html_print_obj(value, str_list, indent)
            str_list.append('</span>')
            str_list.append('<span class="json-comma">,</span>\n')
        if len(array) > 0:
            del str_list[-1]
            str_list.append('\n')

        str_list.append('</span>')
        str_list.append('  ' * (indent - 1))
        str_list.append('<span class="json-close-bracket">]</span>')

class EventExtraMixin(ExtraDataHTMLMixin):
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
        html_piece = self.json_to_html(event.extra_data)
        return html_piece

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
            'extra': extra_data_html,
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
