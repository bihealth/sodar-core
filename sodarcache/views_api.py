"""REST API views for the sodarcache app"""

from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound, ParseError
from rest_framework.generics import RetrieveAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema, inline_serializer

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.views_api import SODARAPIGenericProjectMixin

from sodarcache.serializers import JSONCacheItemSerializer

# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
APP_NAME = 'sodarcache'
SODARCACHE_API_MEDIA_TYPE = (
    'application/vnd.bihealth.sodar-core.sodarcache+json'
)
SODARCACHE_API_DEFAULT_VERSION = '1.0'
SODARCACHE_API_ALLOWED_VERSIONS = ['1.0']


# Base Classes and Mixins ------------------------------------------------------


class SodarcacheAPIViewMixin:
    """
    Sodarcache API view versioning mixin for overriding media type and
    accepted versions, as well as providing helpers
    """

    class SodarcacheAPIRenderer(JSONRenderer):
        media_type = SODARCACHE_API_MEDIA_TYPE

    class SodarcacheAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = SODARCACHE_API_ALLOWED_VERSIONS
        default_version = SODARCACHE_API_DEFAULT_VERSION

    class BackendUnavailable(APIException):
        status_code = 503
        default_detail = 'Cache backend not enabled'
        default_code = 'service_unavailable'

    renderer_classes = [SodarcacheAPIRenderer]
    versioning_class = SodarcacheAPIVersioning

    @classmethod
    def get_backend(cls):
        """
        Return sodarcache backend or raise 503 if not enabled.

        :Return: SodarCacheAPI object
        """
        cache_backend = get_backend_api('sodar_cache')
        if not cache_backend:
            raise cls.BackendUnavailable()
        return cache_backend


# API Views --------------------------------------------------------------------


class CacheItemRetrieveAPIView(
    SodarcacheAPIViewMixin, SODARAPIGenericProjectMixin, RetrieveAPIView
):
    """
    Retrieve a cache item along with its data. Returns 404 if cache item is not
    set.

    **URL:** ``/cache/api/retrieve/{Project.sodar_uuid}/{app_name}/{item_name}``

    **Methods:** ``GET``

    **Returns:**

    - ``project``: Project UUID (string)
    - ``app_name``: Name of app to which the item belongs (string)
    - ``name``: Item name (string)
    - ``data``: Item data (JSON)
    - ``date_modified``: Item modification datetime (YYYY-MM-DDThh:mm:ssZ)
    - ``user``: UUID of user who created the item (string)

    **Version Changes**:

    - ``2.0``: Return ``user`` as UUID instead of ``SODARUserSerializer`` dict
    """

    permission_required = 'sodarcache.get_cache_value'
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = JSONCacheItemSerializer

    def get_object(self):
        """
        Override get_object() to return object by project, app name and name.
        """
        cache_backend = self.get_backend()
        try:
            item = cache_backend.get_cache_item(
                app_name=self.kwargs.get('app_name'),
                name=self.kwargs.get('item_name'),
                project=self.get_project(),
            )
        except Exception as ex:
            raise ParseError(ex)
        if not item:
            raise NotFound()
        return item


@extend_schema(
    responses={
        '200': inline_serializer(
            'UpdateTimeResponse',
            fields={'update_time': serializers.IntegerField()},
        )
    }
)
class CacheItemDateRetrieveAPIView(
    SodarcacheAPIViewMixin, SODARAPIGenericProjectMixin, APIView
):
    """
    Retrieve timestamp of the last update to a cache item. Returns 404 if cache
    item is not set.

    **URL:** ``/cache/api/retrieve/date/{Project.sodar_uuid}/{app_name}/{item_name}``

    **Methods:** ``GET``

    **Returns:**

    - ``update_time``: Update timestamp in seconds since epoch (integer)
    """

    permission_required = 'sodarcache.get_cache_value'
    project_type = PROJECT_TYPE_PROJECT
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        cache_backend = self.get_backend()
        try:
            update_time = cache_backend.get_update_time(
                app_name=self.kwargs.get('app_name'),
                name=self.kwargs.get('item_name'),
                project=self.get_project(),
            )
        except Exception as ex:
            raise ParseError(ex)
        if not update_time:
            raise NotFound()
        return Response({'update_time': update_time}, status=200)


class CacheItemSetAPIView(
    SodarcacheAPIViewMixin, SODARAPIGenericProjectMixin, APIView
):
    """
    Create or update a cache item. Replaces an existing item with the same
    project, app name and item name if previously set. Returns 200 on both a
    successful creation and update.

    **URL:** ``/cache/api/set/{Project.sodar_uuid}/{app_name}/{item_name}``

    **Methods:** ``POST``

    **Parameters:**

    - ``data``: Full item data to be set (JSON)
    """

    http_method_names = ['post']
    permission_required = 'sodarcache.set_cache_value'
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = JSONCacheItemSerializer

    def post(self, request, *args, **kwargs):
        cache_backend = self.get_backend()
        try:
            cache_backend.set_cache_item(
                app_name=self.kwargs.get('app_name'),
                name=self.kwargs.get('item_name'),
                user=self.request.user,
                data=request.data['data'],
                data_type='json',
                project=self.get_project(),
            )
        except Exception as ex:
            raise APIException(ex)
        return Response({'detail': 'ok'}, status=200)
