"""Example REST API views for SODAR Core"""

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.versioning import AcceptHeaderVersioning
from rest_framework.views import APIView

# Projectroles dependency
from projectroles.views_api import SODARAPIGenericProjectMixin


EXAMPLE_API_MEDIA_TYPE = 'application/vnd.bihealth.sodar-core.example+json'
EXAMPLE_API_DEFAULT_VERSION = '1.0'
EXAMPLE_API_ALLOWED_VERSIONS = ['1.0']


class ExampleAPIVersioningMixin:
    """
    Example API view versioning mixin for overriding media type and accepted
    versions.
    """

    class ExampleAPIRenderer(JSONRenderer):
        media_type = EXAMPLE_API_MEDIA_TYPE

    class ExampleAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = EXAMPLE_API_DEFAULT_VERSION
        default_version = EXAMPLE_API_ALLOWED_VERSIONS

    renderer_classes = [ExampleAPIRenderer]
    versioning_class = ExampleAPIVersioning


class HelloExampleProjectAPIView(
    ExampleAPIVersioningMixin, SODARAPIGenericProjectMixin, APIView
):
    """
    Example API view with a project scope.

    **URL:** ``api/hello/{Project.sodar_uuid}``

    **Methods:** ``GET``

    **Returns:**

    - ``detail``: Hello message (string)
    """

    http_method_names = ['get']
    permission_required = 'example_project_app.view_data'

    def get(self, request, *args, **kwargs):
        project = self.get_project()
        return Response(
            {'detail': 'Hello world from project: {}'.format(project.title)},
            status=status.HTTP_200_OK,
        )
