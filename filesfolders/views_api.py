"""REST API views for the samplesheets app"""

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)
from rest_framework.renderers import JSONRenderer
from rest_framework.versioning import AcceptHeaderVersioning

# Projectroles dependency
from projectroles.models import SODAR_CONSTANTS
from projectroles.plugins import get_backend_api
from projectroles.views_api import (
    CoreAPIGenericProjectMixin,
    SODARPageNumberPagination,
)

from filesfolders.models import Folder
from filesfolders.serializers import (
    FolderSerializer,
    FileSerializer,
    HyperLinkSerializer,
)
from filesfolders.views import (
    FilesfoldersTimelineMixin,
    FileServeMixin,
    TL_OBJ_TYPES,
    APP_NAME,
)


# SODAR constants
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']

# Local constants
FILESFOLDERS_API_MEDIA_TYPE = (
    'application/vnd.bihealth.sodar-core.filesfolders+json'
)
FILESFOLDERS_API_DEFAULT_VERSION = '1.0'
FILESFOLDERS_API_ALLOWED_VERSIONS = ['1.0']


# Base Classes and Mixins ------------------------------------------------------


class FilesfoldersAPIVersioningMixin:
    """
    Filesfolders API view versioning mixin for overriding media type and
    accepted versions.
    """

    class FilesfoldersAPIRenderer(JSONRenderer):
        media_type = FILESFOLDERS_API_MEDIA_TYPE

    class FilesfoldersAPIVersioning(AcceptHeaderVersioning):
        allowed_versions = FILESFOLDERS_API_ALLOWED_VERSIONS
        default_version = FILESFOLDERS_API_DEFAULT_VERSION

    renderer_classes = [FilesfoldersAPIRenderer]
    versioning_class = FilesfoldersAPIVersioning


class ListCreateAPITimelineMixin(FilesfoldersTimelineMixin):
    """
    Mixin that ties ListCreateAPIView:s to the SODAR timeline for filesfolders.
    """

    def perform_create(self, serializer):
        # Actually perform the creation
        super().perform_create(serializer)
        # Register creation with timeline
        self.add_item_modify_event(
            obj=serializer.instance, request=self.request, view_action='create'
        )


class RetrieveUpdateDestroyAPITimelineMixin(FilesfoldersTimelineMixin):
    """
    Mixin that ties RetrieveUpdateDestroyAPIView:s to the SODAR timeline for
    filesfolders.
    """

    def perform_update(self, serializer):
        # Collect update_attrs and old_data
        update_attrs = ['name', 'folder', 'description', 'flag']
        old_item = serializer.instance
        old_data = {}

        if old_item.__class__.__name__ == 'HyperLink':
            update_attrs.append('url')
        elif old_item.__class__.__name__ == 'File':
            update_attrs.append('public_url')

        for a in update_attrs:
            old_data[a] = getattr(old_item, a)

        # Actually perform the update
        super().perform_update(serializer)

        # Register update with timeline
        self.add_item_modify_event(
            obj=serializer.instance,
            request=self.request,
            view_action='update',
            update_attrs=update_attrs,
            old_data=old_data,
        )

    def perform_destroy(self, instance):
        instance.delete()
        timeline = get_backend_api('timeline_backend')

        # Add event in Timeline
        if timeline:
            obj_type = TL_OBJ_TYPES[instance.__class__.__name__]
            # Add event in Timeline
            tl_event = timeline.add_event(
                project=instance.project,
                app_name=APP_NAME,
                user=self.request.user,
                event_name='{}_delete'.format(obj_type),
                description='delete {} {{{}}}'.format(obj_type, obj_type),
                status_type='OK',
            )
            tl_event.add_object(
                obj=instance,
                label=obj_type,
                name=(
                    instance.get_path()
                    if isinstance(instance, Folder)
                    else instance.name
                ),
            )


class ListCreatePermissionMixin:
    """Mixing adding get_permission_required() for list-create API views."""

    def get_permission_required(self):
        if self.request.method == 'POST':
            return 'filesfolders.add_data'
        else:
            return 'filesfolders.view_data'


class RetrieveUpdateDestroyPermissionMixin:
    """
    Mixing adding get_permission_required() for retrieve-update-destroy API
    views.
    """

    def get_permission_required(self):
        if self.request.method == 'GET':
            return 'filesfolders.view_data'
        else:
            obj = self.get_object()
            if obj.owner == self.request.user:
                return 'filesfolders.update_data_own'
            else:
                return 'filesfolders.update_data_all'


# API Views --------------------------------------------------------------------


class FolderListCreateAPIView(
    ListCreateAPITimelineMixin,
    ListCreatePermissionMixin,
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    ListCreateAPIView,
):
    """
    List folders or create a folder.

    Supports optional pagination for listing by providing the ``page`` query
    string. This will return results in the Django Rest Framework
    ``PageNumberPagination`` format.

    **URL:** ``/files/api/folder/list-create/{Project.sodar_uuid}``

    **Methods:** ``GET``, ``POST``

    **Parameters for GET:**

    - ``page``: Page number for paginated results (int, optional)

    **Parameters for POST:**

    - ``name``: Folder name (string)
    - ``folder``: Parent folder UUID (string)
    - ``owner``: User UUID of folder owner (string)
    - ``flag``: Folder flag (string, optional)
    - ``description``: Folder description (string, optional)
    """

    pagination_class = SODARPageNumberPagination
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = FolderSerializer


class FolderRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPITimelineMixin,
    RetrieveUpdateDestroyPermissionMixin,
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update or destroy a folder.

    **URL:** ``/files/api/folder/retrieve-update-destroy/{Folder.sodar_uuid}``

    **Methods:** ``GET``, ``PUT``, ``PATCH``, ``DELETE``

    **Parameters for PUT and PATCH:**

    - ``name``: Folder name (string)
    - ``folder``: Parent folder UUID (string)
    - ``owner``: User UUID of folder owner (string)
    - ``flag``: Folder flag (string, optional)
    - ``description``: Folder description (string, optional)
    """

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'folder'
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = FolderSerializer


class FileListCreateAPIView(
    ListCreateAPITimelineMixin,
    ListCreatePermissionMixin,
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    ListCreateAPIView,
):
    """
    List files or upload a file. For uploads, the request must be made in the
    ``multipart`` format.

    Supports optional pagination for listing by providing the ``page`` query
    string. This will return results in the Django Rest Framework
    ``PageNumberPagination`` format.

    **URL:** ``/files/api/file/list-create/{Project.sodar_uuid}``

    **Methods:** ``GET``, ``POST``

    **Parameters for GET:**

    - ``page``: Page number for paginated results (int, optional)

    **Parameters for POST:**

    - ``name``: Folder name (string)
    - ``folder``: Parent folder UUID (string)
    - ``owner``: User UUID of folder owner (string)
    - ``flag``: Folder flag (string, optional)
    - ``description``: Folder description (string, optional)
    - ``public_url``: Allow creation of a publicly viewable URL (bool)
    - ``file``: File to be uploaded
    """

    pagination_class = SODARPageNumberPagination
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = FileSerializer


class FileRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPITimelineMixin,
    RetrieveUpdateDestroyPermissionMixin,
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update or destroy a file.

    **URL:** ``/files/api/file/retrieve-update-destroy/{File.sodar_uuid}``

    **Methods:** ``GET``, ``PUT``, ``PATCH``, ``DELETE``

    **Parameters for PUT and PATCH:**

    - ``name``: Folder name (string)
    - ``folder``: Parent folder UUID (string)
    - ``owner``: User UUID of folder owner (string)
    - ``flag``: Folder flag (string, optional)
    - ``description``: Folder description (string, optional)
    - ``public_url``: Allow creation of a publicly viewable URL (bool)
    - ``file``: File to be uploaded
    """

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'file'
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = FileSerializer


class FileServeAPIView(
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    FileServeMixin,
    GenericAPIView,
):
    """
    Serve the file content.

    **URL:** ``/files/api/file/serve/{File.sodar_uuid}``

    **Methods:** ``GET``
    """

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'file'
    permission_required = 'filesfolders.view_data'


class HyperLinkListCreateAPIView(
    ListCreateAPITimelineMixin,
    ListCreatePermissionMixin,
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    ListCreateAPIView,
):
    """
    List hyperlinks or create a hyperlink.

    Supports optional pagination for listing by providing the ``page`` query
    string. This will return results in the Django Rest Framework
    ``PageNumberPagination`` format.

    **URL:** ``/files/api/hyperlink/list-create/{Project.sodar_uuid}``

    **Methods:** ``GET``, ``POST``

    **Parameters for GET:**

    - ``page``: Page number for paginated results (int, optional)

    **Parameters for POST:**

    - ``name``: Folder name (string)
    - ``folder``: Parent folder UUID (string)
    - ``owner``: User UUID of folder owner (string)
    - ``flag``: Folder flag (string, optional)
    - ``description``: Folder description (string, optional)
    - ``url``: URL for the link (string)
    """

    pagination_class = SODARPageNumberPagination
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = HyperLinkSerializer


class HyperLinkRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPITimelineMixin,
    RetrieveUpdateDestroyPermissionMixin,
    FilesfoldersAPIVersioningMixin,
    CoreAPIGenericProjectMixin,
    RetrieveUpdateDestroyAPIView,
):
    """
    Retrieve, update or destroy a hyperlink.

    **URL:** ``/files/api/hyperlink/retrieve-update-destroy/{HyperLink.sodar_uuid}``

    **Methods:** ``GET``, ``PUT``, ``PATCH``, ``DELETE``

    **Parameters for PUT and PATCH:**

    - ``name``: Folder name (string)
    - ``folder``: Parent folder UUID (string)
    - ``owner``: User UUID of folder owner (string)
    - ``flag``: Folder flag (string, optional)
    - ``description``: Folder description (string, optional)
    - ``url``: URL for the link (string)
    """

    lookup_field = 'sodar_uuid'
    lookup_url_kwarg = 'hyperlink'
    project_type = PROJECT_TYPE_PROJECT
    serializer_class = HyperLinkSerializer
