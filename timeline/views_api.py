"""REST API views for the timeline app"""

from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.versioning import AcceptHeaderVersioning

# Projectroles dependency
from projectroles.views_api import (
    SODARAPIGenericProjectMixin,
    SODARPageNumberPagination,
)

from timeline.models import TimelineEvent
from timeline.serializers import TimelineEventSerializer


# Local constants
TIMELINE_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core.timeline+json'
TIMELINE_API_DEFAULT_VERSION = '2.0'
TIMELINE_API_ALLOWED_VERSIONS = ['2.0']


class TimelineAPIVersioningMixin:
    """
    Timeline API view versioning mixin for overriding media type and
    accepted versions.
    """

    class TimelineAPIRenderer(JSONRenderer):
        media_type = TIMELINE_API_MEDIA_TYPE

    class TimelineAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = TIMELINE_API_ALLOWED_VERSIONS
        default_version = TIMELINE_API_DEFAULT_VERSION

    renderer_classes = [TimelineAPIRenderer]
    versioning_class = TimelineAPIVersioning


class ProjectTimelineEventListAPIView(
    TimelineAPIVersioningMixin, SODARAPIGenericProjectMixin, ListAPIView
):
    """
    List ``TimelineEvent`` objects belonging in a category or project. Events
    are ordered from newest to oldest.

    Supports optional pagination by providing the ``page`` query string. This
    will return results in the Django Rest Framework PageNumberPagination
    format.

    **URL:** ``/timeline/api/list/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Parameters:**

    - ``page``: Page number for paginated results (int, optional)

    **Returns:** List or paginated dict of ``TimelineEvent`` objects (see ``TimelineEventRetrieveAPIView``)
    """

    pagination_class = SODARPageNumberPagination
    permission_required = 'timeline.view_timeline'
    serializer_class = TimelineEventSerializer

    def get_queryset(self):
        project = self.get_project()
        user = self.request.user
        q_kwargs = {'project': project}
        if not user.is_superuser and not project.is_owner_or_delegate(user):
            q_kwargs['classified'] = False
        return TimelineEvent.objects.filter(**q_kwargs).order_by('-pk')


class SiteTimelineEventListAPIView(TimelineAPIVersioningMixin, ListAPIView):
    """
    List site-wide ``TimelineEvent`` objects. Events are ordered from newest to
    oldest.

    Supports optional pagination by providing the ``page`` query string. This
    will return results in the Django Rest Framework ``PageNumberPagination``
    format.

    **URL:** ``/timeline/api/list/site``

    **Methods:** ``GET``

    **Parameters:**

    - ``page``: Page number for paginated results (int, optional)

    **Returns:** List or paginated dict of ``TimelineEvent`` objects (see ``TimelineEventRetrieveAPIView``)
    """

    pagination_class = SODARPageNumberPagination
    permission_classes = [IsAuthenticated]
    serializer_class = TimelineEventSerializer

    def get_queryset(self):
        user = self.request.user
        q_kwargs = {'project': None}
        if not user.is_superuser:
            q_kwargs['classified'] = False
        return TimelineEvent.objects.filter(**q_kwargs).order_by('-pk')


class TimelineEventRetrieveAPIView(TimelineAPIVersioningMixin, RetrieveAPIView):
    """
    Retrieve ``TimelineEvent`` object.

    Extra data is only returned for users with sufficient permissions
    (superusers, project owners and delegates).

    **URL:** ``/timeline/api/retrieve/{TimelineEvent.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``project``: Project UUID (string or None)
    - ``app``: App name (string)
    - ``user``: UUID of user who created the event (string or None)
    - ``event_name``: Event name (string)
    - ``description``: Event description (string)
    - ``extra_data``: Event extra data (JSON or None)
    - ``classified``: Whether event is classified (boolean)
    - ``status_changes``: List of TimelineEventStatus objects (JSON)
        - ``event``: TimelineEvent UUID (string)
        - ``timestamp``: Status datetime (YYYY-MM-DDThh:mm:ssZ)
        - ``status_type``: Status type (string)
        - ``description``: Status description (string)
        - ``extra_data``: Status extra data (JSON or None)
        - ``sodar_uuid``: Status UUID (string)
    - ``event_objects``: List of TimelineEventObjectRef objects (JSON)
        - ``event``: TimelineEvent UUID (string)
        - ``label``: Object label as given in event description (string)
        - ``name``: Name for identifying the object (string)
        - ``object_uuid``: UUID of the referred object (string)
        - ``extra_data``: Object reference extra data (JSON or None)
        - ``sodar_uuid``: Object reference UUID (string)
    - ``sodar_uuid``: TimelineEvent UUID (string)

    **Version Changes:**

    - ``2.0``: Return ``user`` as UUID instead of ``SODARUserSerializer`` dict
    """

    permission_classes = [IsAuthenticated]  # Perms checked in get_object()
    serializer_class = TimelineEventSerializer

    def get_object(self):
        obj = TimelineEvent.objects.filter(
            sodar_uuid=self.kwargs.get('timelineevent')
        ).first()
        if not obj:
            raise NotFound()
        user = self.request.user
        if obj.project and not user.has_perm(
            'timeline.view_timeline', obj.project
        ):
            raise PermissionDenied()
        if obj.classified:
            if (
                obj.project
                and not user.is_superuser
                and not obj.project.is_owner_or_delegate(user)
            ):
                raise PermissionDenied()
            elif not obj.project and not user.is_superuser:
                raise PermissionDenied()
        return obj
